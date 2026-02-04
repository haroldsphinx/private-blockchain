# zama-pevm-testnet

Private Ethereum testnet running geth (EL) + lighthouse (CL) via [Kurtosis](https://www.kurtosis.com/). Monitoring with Prometheus, Grafana, Loki, and AlertManager. See [Notes.md](Notes.md) for design decisions.

## Local setup

Requires: docker, [kurtosis](https://docs.kurtosis.com/install/), docker compose

```sh
./k8s/scripts/setup.sh
```

## AWS setup

Requires: terraform, AWS credentials configured (`aws configure` or env vars)

```sh
cd terraform/environments/testnet
terraform init
terraform apply
```

SSH in and watch the bootstrap:
```sh
ssh ubuntu@<PUBLIC_IP> 'sudo tail -f /var/log/cloud-init-output.log'
```

## Services

Public endpoints (via nginx reverse proxy):

| Port | Service | URL |
| --- | --- | --- |
| 8545 | JSON-RPC | `http://<IP>:8545` |
| 3000 | Grafana | `http://<IP>:3000` (admin/admin) |
| 9090 | Prometheus | `http://<IP>:9090` |
| 9094 | AlertManager | `http://<IP>:9094` |

Test RPC:
```sh
curl -X POST http://<IP>:8545 \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
```

Internal Kurtosis services (localhost only):
```sh
kurtosis enclave inspect zama-testnet
```

## Network

Defined in `kurtosis/network_params.yaml`:
- 2 validator nodes (geth + lighthouse, 32 keys each)
- 1 RPC node (geth + lighthouse, no validators)
- Assertoor for automated network validation
- Blockscout block explorer

## Monitoring

Two monitoring layers:

1. **Kurtosis built-in** — Prometheus + Grafana deployed inside the enclave (ports in 36000 range)
2. **Observability stack** — Custom docker-compose with Prometheus, Grafana, Loki, Promtail, AlertManager, Blackbox Exporter, Node Exporter (ports 3001, 9091, 9093)

Alerts: ELNodeDown, CLNodeDown, PeerCountLow, NoNewBlocks, RPCDown, ChainNotSynced.

## CI

| Workflow | What |
| --- | --- |
| `validate-network.yml` | RPC health checks against deployed testnet |
| `infra.yml` | Terraform plan/apply |

The validation workflow checks: RPC response, block production, peer connectivity, sync status, chain ID.

## Teardown

Local:
```sh
cd observability && docker compose down
kurtosis enclave rm -f zama-testnet
```

AWS:
```sh
cd terraform/environments/testnet
terraform destroy
```
