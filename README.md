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

Kurtosis binds all services to `0.0.0.0` on fixed ports (`port_publisher`). Get the full map with:

```sh
kurtosis enclave inspect zama-testnet
```

| Port range | What |
| --- | --- |
| `32000+` | geth nodes (rpc, ws, metrics, discovery) |
| `33000+` | lighthouse nodes (http, metrics, discovery) |
| `34000+` | validator clients |
| `36000+` | blockscout, grafana, prometheus, assertoor |
| `3001` | observability grafana (admin/admin) |
| `9091` | observability prometheus |
| `9093` | alertmanager |

```sh
curl -X POST http://<IP>:<EL3_RPC_PORT> \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
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

| Workflow | Backend | Timeout |
| --- | --- | --- |
| `validate-network.yml` | Docker | 45 min |
| `validate-k8s.yml` | Minikube | 60 min |
| `infra.yml` | Terraform | plan only |

Both network workflows deploy the chain and run Assertoor validation. Enclave logs are uploaded as artifacts on failure.

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
