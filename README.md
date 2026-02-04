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

| Port | Service |
| --- | --- |
| 32017 | JSON-RPC |
| 36001 | Blockscout |
| 3000 | Grafana (admin/admin) |
| 9090 | Prometheus |
| 9093 | AlertManager |

Test RPC:
```sh
curl -X POST http://<IP>:32017 \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
```

Kurtosis services:
```sh
kurtosis enclave inspect zama-testnet
```

## Network

Defined in `kurtosis/network_params.yaml`:
- 2 validator nodes (geth + lighthouse, 32 keys each)
- 1 RPC node (geth + lighthouse, no validators)
- Blockscout block explorer

## Monitoring

Observability stack (Prometheus, Grafana, AlertManager) deployed via cloud-init.

Alerts configured: ELNodeDown, CLNodeDown, NoNewBlocks.

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
