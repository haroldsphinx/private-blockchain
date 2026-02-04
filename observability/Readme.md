# Observability

Local dev monitoring stack. Used with `k8s/scripts/setup.sh` for single-VM Kurtosis testing.

```sh
cd observability
docker compose up -d
```

For AWS deployment, monitoring runs on a dedicated VM provisioned by Terraform.
