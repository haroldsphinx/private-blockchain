#!/bin/bash
# Bootstrap zama-pevm-testnet on minikube.
# Requires: minikube, kubectl, helm, kurtosis

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENCLAVE_NAME="zama-testnet"
DOMAIN="haroldsphinx.com"

if minikube status --format='{{.Host}}' 2>/dev/null | grep -q "Running"; then
  echo "minikube already running"
else
  minikube start \
    --cpus=4 \
    --memory=8192 \
    --disk-size=40g \
    --driver=docker
fi

minikube addons enable ingress
kubectl wait --for=condition=available deployment/ingress-nginx-controller \
  -n ingress-nginx --timeout=120s

# argocd
kubectl create namespace argocd 2>/dev/null || true
helm repo add argo https://argoproj.github.io/argo-helm 2>/dev/null || true
helm repo update
helm upgrade --install argocd argo/argo-cd \
  --namespace argocd \
  --values "$REPO_ROOT/k8s/argocd/argocd-values.yaml" \
  --wait --timeout 5m

# deploy the network
kurtosis cluster set kube
kurtosis engine restart
kurtosis gateway &
GATEWAY_PID=$!
sleep 5

kurtosis run \
  --enclave "$ENCLAVE_NAME" \
  github.com/ethpandaops/ethereum-package \
  --args-file "$REPO_ROOT/kurtosis/network_params.yaml"

kurtosis enclave inspect "$ENCLAVE_NAME"

# observability + ingress
kubectl apply -f "$REPO_ROOT/k8s/argocd/apps/observability.yaml"
kubectl wait --for=condition=available deployment/argocd-server \
  -n argocd --timeout=120s 2>/dev/null || true
kubectl apply -f "$REPO_ROOT/k8s/ingress/ingress.yaml"

MINIKUBE_IP=$(minikube ip)
ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" 2>/dev/null | base64 -d || echo "n/a")

echo ""
echo "add to /etc/hosts:"
echo "  $MINIKUBE_IP rpc.$DOMAIN explorer.$DOMAIN grafana.$DOMAIN argocd.$DOMAIN"
echo ""
echo "services:"
echo "  rpc:      http://rpc.$DOMAIN"
echo "  explorer: http://explorer.$DOMAIN"
echo "  grafana:  http://grafana.$DOMAIN (admin/admin)"
echo "  argocd:   http://argocd.$DOMAIN (admin/$ARGOCD_PASSWORD)"
echo ""
echo "teardown:"
echo "  kurtosis enclave rm -f $ENCLAVE_NAME && minikube delete"
