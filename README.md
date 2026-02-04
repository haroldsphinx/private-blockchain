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

| Endpoint | What |
| --- | --- |
| `http://<IP>:8545` | geth JSON-RPC (dedicated RPC node) |
| `http://<IP>:3000` | Grafana (admin/admin) |
| `http://<IP>:9090` | Prometheus |

Locally, the RPC port is dynamically assigned by Kurtosis — `setup.sh` prints it at the end.

```sh
curl -X POST http://<IP>:8545 \
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

Prometheus + Grafana + Loki + AlertManager via docker-compose in `observability/`.

Alerts: ELNodeDown, CLNodeDown, PeerCountLow, NoNewBlocks, RPCDown, ChainNotSynced.

The setup script extracts Kurtosis-assigned ports and writes them to `observability/.env` so Prometheus can scrape the nodes.

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
