# zama-pevm-testnet

Private ethereum testnet running geth (EL) + lighthouse (CL) on Kubernetes via Kurtosis. ArgoCD manages the observability stack. See [Notes.md](Notes.md) for design decisions and trade-offs.

## Deploy locally

Requires: minikube, kubectl, helm, kurtosis

```sh
./k8s/scripts/setup.sh
```

Add to `/etc/hosts`:
```
<MINIKUBE_IP> rpc.haroldsphinx.com explorer.haroldsphinx.com grafana.haroldsphinx.com argocd.haroldsphinx.com
```

## Deploy on AWS

```sh
cd terraform/environments/testnet
terraform init
terraform apply
```

Point `*.haroldsphinx.com` to the instance public IP. Cloud-init handles the full bootstrap (~10-15 min on first boot).

## Services

| URL | What |
| --- | --- |
| `http://rpc.haroldsphinx.com` | geth JSON-RPC (dedicated RPC node, no validators) |
| `http://explorer.haroldsphinx.com` | Blockscout |
| `http://grafana.haroldsphinx.com` | Grafana (admin/admin) |
| `http://argocd.haroldsphinx.com` | ArgoCD (admin / see bootstrap output) |

Direct RPC fallback: `http://<IP>:8545`

```sh
curl -X POST http://rpc.haroldsphinx.com \
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

kube-prometheus-stack via ArgoCD. Prometheus auto-discovers kurtosis pods on `kt-*` namespaces.

Alerts: ELNodeDown, CLNodeDown, PeerCountLow, NoNewBlocks.

## CI

| Workflow | Backend | Timeout |
| --- | --- | --- |
| `validate-network.yml` | Docker | 45 min |
| `validate-k8s.yml` | Minikube | 60 min |

Both deploy the network and run Assertoor validation. Enclave logs uploaded as artifacts on failure.

## Teardown

```sh
kurtosis enclave rm -f zama-testnet
minikube delete
```
