# Notes

## Why Kurtosis

Went with Kurtosis because the ethereum testing community already converged on it. The ethereum-package by ethpandaops is what most public testnets use — battle-tested tooling. Writing my own docker-compose for geth+lighthouse would take longer and I'd end up reimplementing what Kurtosis already does: genesis generation, validator key distribution, bootnode discovery.

## Network Topology

Current setup: 3 VMs, each running one blockchain node.

- node-1: validator (32 keys), acts as bootnode
- node-2: validator (32 keys)
- node-3: RPC node, runs blockscout

All nodes share the same genesis files (committed to repo) and peer via P2P. The RPC node has no validator keys — it just syncs from peers and serves JSON-RPC. This separation keeps public traffic off validators.

## The Multi-VM Evolution

Started with everything on one EC2 instance running a single Kurtosis enclave. Worked fine but nodes couldn't peer across VMs since each enclave generates its own genesis.

Fell into a bit of an improvement rabbit hole here. The fix was straightforward: generate genesis once locally, commit to repo, have each VM clone and use the same genesis. Replaced Kurtosis-on-VM with direct docker-compose (geth + lighthouse). Node-1's nodekey is pre-generated so its enode is deterministic — other nodes can reference it as bootnode.

The `k8s/` directory still has the original single-VM Kurtosis setup. It works for local dev (`./k8s/scripts/setup.sh`) but drifted from the AWS multi-VM architecture. Didn't remove it since it's still useful for quick local testing.

## Infrastructure

Terraform provisions:
- VPC with public subnet
- 3 blockchain EC2 instances (one per node)
- 1 monitoring EC2 instance
- Elastic IPs for all

Cloud-init on each blockchain VM:
1. Clones repo to get genesis files
2. Initializes geth with shared genesis
3. Imports validator keys (if validator role)
4. Starts docker-compose with node-specific env vars

## Observability

Monitoring runs on a dedicated instance: Prometheus, Grafana, Loki, AlertManager.

Each blockchain node runs [Telescope](https://github.com/blockopsnetwork/telescope) — an observability agent I built for blockchain infrastructure. It scrapes geth/lighthouse metrics and ships them to Prometheus via remote write. Also collects container logs and pushes to Loki.

Alerts: ELNodeDown, CLNodeDown, NoNewBlocks.

## AI Assistance

Used Claude Code (coding agent) to help with parts of this. Being upfront about it.

Specifically `scripts/generate-genesis.sh` — the key splitting logic and kurtosis file extraction. I reviewed and tested it, but the boilerplate was AI-assisted. The architectural decisions (shared genesis approach, bootnode setup, multi-VM topology) were mine.

The terraform modules under `terraform/modules/` are ones I had from previous projects, just reused them here.

## What I'd do differently for production

**Load balancer.** The diagram shows a proxy/LB but I didn't set one up. For production: ALB in front of RPC nodes, health checks on `/health`, sticky sessions disabled since RPC is stateless, WAF rules to rate-limit and block malicious payloads.

**Managed Kubernetes.** EKS with proper node pools. The docker-compose approach works for a testnet but doesn't scale.

**Multiple AZs.** Spread validators across availability zones.

**Secrets management.** Validator keys through AWS Secrets Manager, not committed to repo.

**Persistent storage.** EBS-backed volumes for chain data.

**DNS + TLS.** Route53 with cert-manager.

## Trade-offs

- Committing genesis to git is fine for a testnet, not for production (keys in repo)
- Cloud-init is one-shot — failed bootstrap means destroy and recreate
- Docker backend means no k8s features (rolling updates, self-healing)
- Pre-generated nodekeys mean deterministic enodes but also mean those keys are in the repo

## Repo Layout

```
scripts/                   genesis generation
docker/                    docker-compose for blockchain nodes
genesis/                   shared genesis files (generated)
kurtosis/                  network params for genesis generation
k8s/                       local dev setup (single-VM, drifted from AWS)
terraform/
  environments/testnet/    multi-VM infrastructure
  modules/compute/         reusable EC2 module
observability/             local monitoring stack
.github/workflows/         CI
```
