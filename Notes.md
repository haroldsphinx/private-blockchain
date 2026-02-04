# Notes

## Why Kurtosis

I went with Kurtosis because the ethereum testing community already converged on it. The `ethpandaops/ethereum-package` is what most public testnets use (Holesky, Dencun testing, etc.), so the tooling is battle-tested. Writing my own docker-compose or helm chart for geth+lighthouse would have taken longer and given me a worse result — Kurtosis handles genesis generation, validator key distribution, bootnode discovery, and service wiring out of the box.

The other thing Kurtosis gives me is backend portability. Same `network_params.yaml` works on Docker (for quick local testing or CI) and on Kubernetes (for anything resembling production). I didn't have to maintain two separate deployment configs.

## Network topology

Two validator nodes (32 keys each, 64 total) and one dedicated RPC node with no validator keys. The validators produce and attest blocks, the RPC node syncs from them over P2P and serves external JSON-RPC traffic. This separation matters — you don't want public RPC traffic hitting your validators directly. The RPC node also proves that P2P sync works, since it has no local state production of its own.

I disabled the Fulu fork by setting its epoch to uint64 max. Fulu needs 128+ validators or supernodes, which is overkill for a testnet with 64 validators. Electra is enabled at epoch 0.

## Infrastructure

Terraform provisions a VPC + EC2 instance on AWS. The instance runs minikube, which runs everything else. I know minikube on EC2 sounds weird — it's an extra layer — but it means the local dev setup and the cloud setup are the same stack. `setup.sh` and cloud-init run the same sequence: start minikube, install ArgoCD, deploy via Kurtosis, apply ingress. One `network_params.yaml` drives both.

The cloud-init template uses `templatefile()` to inject the actual repo config files (network params, ArgoCD values, observability app, ingress manifests) at plan time. No copy-pasting configs into the template — change a file in the repo and both deployment paths pick it up.

## Why cloud-init instead of Ansible

For a single EC2 instance that needs to go from bare Ubuntu to fully running testnet, cloud-init is simpler. There's no control plane to manage, no inventory file, no SSH key bootstrapping chicken-and-egg problem. The instance provisions itself on first boot.

Ansible would make more sense if I had multiple instances to configure, or if I needed to do incremental config changes on running hosts. For this case — one instance, one-shot setup — cloud-init is the right tool. It's also natively supported by EC2, no extra dependencies.

If this were a production setup with a fleet of nodes, I'd use Ansible (or more likely, just run a proper managed k8s cluster and skip the VM provisioning entirely).

## Observability

The monitoring stack is kube-prometheus-stack deployed via ArgoCD. Prometheus discovers kurtosis pods using `kubernetes_sd_configs` on `kt-*` namespaces — no hardcoded endpoints or port numbers. When Kurtosis creates or recreates the enclave, Prometheus picks up the new pods automatically.

Four alert rules: execution node down, consensus node down, peer count low, no new blocks. These cover the basics — is the network alive, are nodes talking to each other, are blocks being produced.

I started with a standalone docker-compose monitoring stack (the `observability/` directory) during early development when I was running Kurtosis on the Docker backend. Once I moved to Kubernetes, it made more sense to use kube-prometheus-stack managed by ArgoCD. The standalone configs are still in the repo for reference.

## CI / QA

Two GitHub Actions workflows:

- `validate-network.yml` runs Kurtosis on the Docker backend. Faster, good for quick validation.
- `validate-k8s.yml` runs Kurtosis on minikube inside the runner. Slower, but validates the actual Kubernetes deployment path.

Both deploy the network using the same `network_params.yaml`, then use the `ethpandaops/assertoor-github-action` for validation. Assertoor is also deployed inside the enclave as an `additional_service` — it runs a suite of checks against the live network (nodes synced, blocks produced, transactions land). The GitHub Action polls Assertoor's API and turns the results into a CI pass/fail.

On failure, both workflows dump the full enclave logs and k8s state as artifacts for debugging.

## What I'd do differently for production

**Managed Kubernetes.** Running minikube on EC2 works for a testnet, but production would use EKS (or equivalent). Proper node pools, autoscaling, managed control plane.

**Multiple physical nodes.** Right now everything runs on one instance. A real setup would spread validators across availability zones, separate the RPC tier, and run the monitoring stack on its own infrastructure.

**DNS and TLS.** I'm using `*.haroldsphinx.com` with manual DNS pointing. Production would use Route53 (or external-dns) with cert-manager for automatic Let's Encrypt certificates.

**Secrets management.** Validator keys and Grafana/ArgoCD credentials would go through AWS Secrets Manager or Vault, not inline defaults.

**Persistent storage.** Geth and Lighthouse data should survive pod restarts. That means PVCs backed by EBS or similar. Right now if the enclave is destroyed, the chain state is gone.

**Log aggregation.** Promtail/Loki or shipping logs to CloudWatch. Right now logs are only in the pod stdout and the kurtosis enclave dump.

**Alerting destinations.** The alert rules exist but Alertmanager isn't configured to route anywhere. Production would send to Slack, PagerDuty, or similar.

## Trade-offs

- Kurtosis adds a dependency. If it breaks or changes its API, the deployment breaks. But the alternative (writing custom helm charts for geth+lighthouse) is significantly more work for the same result.

- Minikube on EC2 is an extra layer of abstraction. But it buys me dev/prod parity with zero additional config files.

- Cloud-init is one-shot. If the bootstrap fails halfway, you have to destroy and recreate the instance. Ansible would let you re-run. For a testnet this is fine; for production it's not.

- Single `network_params.yaml` for both CI and deployment means CI runs the full 3-node topology. This makes CI slower but means I'm actually testing what gets deployed.

## Repo layout

```
kurtosis/                  network params (single source of truth)
k8s/
  scripts/setup.sh         local minikube bootstrap
  argocd/                  ArgoCD helm values + app definitions
  ingress/                 nginx ingress routes
terraform/
  environments/testnet/    VPC, EC2, cloud-init template
  modules/compute/         reusable EC2 module
observability/             standalone docker-compose stack (legacy/dev)
.github/workflows/         CI pipelines
```
