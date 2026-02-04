# Notes

## Why Kurtosis

I went with Kurtosis because the ethereum testing community already converged on it. The ethereum-package by eth-panda-ops team is what most public testnets use so the tooling is battle-tested, writing my own docker-compose or helm chart for geth+lighthouse would have taken longer. Kurtosis handles genesis generation, validator key distribution, bootnode discovery, and service wiring out of the box.

The other thing Kurtosis gives me is backend portability. Same `network_params.yaml` works on Docker and on Kubernetes. I didn't have to maintain two separate deployment configs.

## Blockchain Network topology

Two validator nodes (32 keys each, 64 total) and one dedicated RPC node with no validator keys. The validators produce and attest blocks, the RPC node syncs from them over P2P and serves external JSON-RPC traffic. this separattion of concerns allows me prevent public RPC traffic from hitting myvalidators directly. The RPC node also proves that P2P sync works, since it has no local state production of its own. (note: I disabled the Fulu fork by setting its epoch to uint64 max)

## Infrastructure

Terraform provisions a VPC + EC2 instance on AWS. Cloud-init bootstraps Docker, installs Kurtosis, deploys the network, and starts the observability stack — all in a single `terraform apply`.

### The Kubernetes detour

My initial approach was to run Kurtosis on Kubernetes (minikube on EC2). The idea was to show k8s workflows: ArgoCD for GitOps, kube-prometheus-stack for monitoring with automatic pod discovery, nginx ingress for service routing. I had it all wired up — ArgoCD managing the observability stack, Prometheus auto-discovering Kurtosis pods via `kubernetes_sd_configs`, ingress rules for RPC, Grafana, and Blockscout.

The problem was reliability. Bootstrapping minikube inside an EC2 instance via cloud-init introduced a fragile dependency chain:

1. **Kurtosis engine failed to start on the k8s backend.** The logs collector daemon set couldn't schedule pods in time. Kurtosis retries 30 times waiting for a pod to come online, then gives up. The root cause was a race condition — `kurtosis cluster set minikube && kurtosis engine restart` ran before the k8s cluster was fully ready to schedule new workloads. Even after adding explicit `kubectl wait` guards, the daemon set scheduling remained flaky on a resource-constrained single-node cluster.

2. **Resource contention.** Running minikube (its own Docker-in-Docker layer), plus the Kurtosis engine pods, plus 3 geth nodes, 3 lighthouse nodes, Blockscout, ArgoCD, kube-prometheus-stack, and nginx ingress on a single t3.xlarge (4 vCPU, 16GB) led to OOM kills and scheduling failures. The minikube VM alone consumed a chunk of the available resources before any workloads started.

3. **Cloud-init is one-shot.** The bootstrap script runs with `set -euo pipefail`. When Kurtosis engine start failed, the entire bootstrap aborted — no network, no monitoring, no recovery without destroying and recreating the instance. Ansible or a more sophisticated retry mechanism could help, but that adds complexity for a problem that shouldn't exist in the first place.

### The decision

Since the goal is a working testnet from a single `terraform apply`, not a demonstration of running k8s on a single VM, I switched the EC2 deployment to the Docker backend. Kurtosis on Docker is what it was designed for — no intermediate orchestration layer, no daemon set scheduling, no resource overhead from a nested container runtime.

The Kubernetes manifests (ArgoCD apps, ingress rules, the k8s CI workflow) are still in the repo. They work and are tested in CI via `validate-k8s.yml` which runs on minikube inside a GitHub Actions runner (where resources are more predictable). This keeps the k8s deployment path validated without making it the critical path for the actual testnet.

## Why cloud-init instead of Ansible

For a single EC2 instance that needs to go from bare Ubuntu to fully running testnet, cloud-init is simpler. There's no control plane to manage, no inventory file, no SSH key bootstrapping chicken-and-egg problem. The instance provisions itself on first boot

Ansible would make more sense if I had multiple instances to configure, or if I needed to do incremental config changes on running hosts. For this case, one instance, one shot setup, cloud-init is the right tool. It's also natively supported by EC2, no extra dependencies needed

If this were a production setup with a fleet of nodes, I'd use Ansible (or more likely, just run a proper managed k8s cluster and skip the VM provisioning entirely)

## Observability

The monitoring stack runs as docker-compose alongside the Kurtosis network. Prometheus, Grafana, Loki, Promtail, AlertManager, Blackbox Exporter, and Node Exporter.

Since Kurtosis assigns dynamic ports to services via its gateway, the setup script extracts the actual port mappings from `kurtosis enclave inspect` and writes them to `observability/.env`. The docker-compose prometheus service uses `sed` to substitute these into the prometheus config template at startup.

Six alert rules: execution node down, consensus node down, peer count low, no new blocks, RPC endpoint down, chain falling behind. These cover the basics: is the network alive, are nodes talking to each other, are blocks being produced, can external clients reach the RPC.

The k8s deployment path uses kube-prometheus-stack via ArgoCD with `kubernetes_sd_configs` for automatic pod discovery — no port extraction needed since Prometheus runs inside the same cluster. That config is in `k8s/argocd/apps/observability.yaml`.

## CI / QA

Two GitHub Actions workflows for network validation:

- `validate-network.yml` runs Kurtosis on the Docker backend. Faster, good for quick validation.
- `validate-k8s.yml` runs Kurtosis on minikube inside the runner. Slower, but validates the Kubernetes deployment path.

Both deploy the network using the same `network_params.yaml`, then use the `ethpandaops/assertoor-github-action` for validation. Assertoor is also deployed inside the enclave as an `additional_service`, it runs a suite of checks against the live network (nodes synced, blocks produced, transactions land), the GitHub action polls assertoor's api and turns the results into a CI pass/fail.

On failure, both workflows dump the full enclave logs (and k8s state for the minikube path) as artifacts for debugging.

A third workflow (`infra.yml`) runs `terraform fmt`, `validate`, and `plan` on every push to verify the infrastructure code stays valid. Apply is intentionally skipped in CI — I'd use Atlantis for that in a real setup.

## What I'd do differently for production

**Managed Kubernetes.** The Docker backend works for a testnet, but production would use EKS (or equivalent). Proper node pools, autoscaling, managed control plane. The k8s manifests in this repo are a starting point for that path.

**Multiple physical nodes.** Right now everything runs on one instance. A real setup would spread validators across availability zones, separate the RPC tier, and run the monitoring stack on its own infrastructure.

**DNS and TLS.** Production would use Route53 (or external-dns) with cert-manager for automatic lets encrypts certificates.

**Secrets management.** Validator keys, grafana credentials would go through AWS Secrets Manager or Vault, not inline defaults.

**Persistent storage.** Geth and Lighthouse data should survive restarts. On k8s that means PVCs backed by EBS with a pvc-autoresizer to handle chain growth. On Docker, named volumes with backup.

**Log aggregation.** Promtail shipping container logs to Loki, queryable through Grafana. The stack is configured for this but needs the Kurtosis container labels to be properly matched in the promtail config.

**Alerting destinations.** Alerts go to AlertManager's default receiver for now. Production would add Slack or PagerDuty with escalation policies.

## Trade-offs

- Kurtosis adds a dependency. If it breaks or changes its API, the deployment breaks. But the alternative (writing custom helm charts for geth+lighthouse) is significantly more work for the same result.

- Docker backend on EC2 means no k8s features (rolling updates, self-healing pods, service mesh). For a testnet that's rebuilt from scratch, this is fine. For long-lived infrastructure it's not.

- Cloud-init is one-shot. If the bootstrap fails halfway, you have to destroy and recreate the instance. Ansible would let you re-run. For a testnet this is fine; for production I wouldn't do that.

- Single `network_params.yaml` for both CI and deployment means CI runs the full 3-node topology. This makes CI slower but means I'm actually testing what gets deployed.

## Repo layout

```
kurtosis/                  network params (single source of truth)
k8s/
  scripts/setup.sh         local bootstrap (Docker backend)
  argocd/                  ArgoCD helm values + app definitions (k8s path)
  ingress/                 nginx ingress routes (k8s path)
  zama-pevm-testnet-job/   Kurtosis deployer k8s job
terraform/
  environments/testnet/    VPC, EC2, cloud-init template
  modules/compute/         reusable EC2 module
observability/             docker-compose monitoring stack
.github/workflows/         CI pipelines
```
