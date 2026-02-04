# Observability

Standalone docker-compose stack used during early development. The production setup uses kube-prometheus-stack deployed via ArgoCD (see `k8s/argocd/apps/observability.yaml`).

To run standalone:

```sh
cd observability
docker compose up -d
```

Note: the prometheus.yml has placeholder ports (`__EL_METRICS_PORT__` etc.) that need to be replaced with actual kurtosis-assigned ports before use.
