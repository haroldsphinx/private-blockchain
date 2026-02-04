#!/bin/bash
# Bootstrap zama-pevm-testnet locally using Kurtosis (Docker backend).
# Requires: docker, kurtosis, docker compose

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENCLAVE_NAME="zama-testnet"

kurtosis engine start

if kurtosis enclave inspect "$ENCLAVE_NAME" &>/dev/null; then
  echo "enclave $ENCLAVE_NAME already exists, skipping deployment"
else
  kurtosis run \
    --enclave "$ENCLAVE_NAME" \
    github.com/ethpandaops/ethereum-package \
    --args-file "$REPO_ROOT/kurtosis/network_params.yaml"
fi

kurtosis enclave inspect "$ENCLAVE_NAME"

# extract dynamic ports assigned by kurtosis
get_port() {
  kurtosis service inspect "$ENCLAVE_NAME" "$1" | grep "$2:" | sed -n 's/.*127\.0\.0\.1:\([0-9]*\).*/\1/p' | head -1
}
EL_METRICS_PORT=$(get_port el-1-geth-lighthouse metrics)
CL_METRICS_PORT=$(get_port cl-1-lighthouse-geth metrics)
EL_RPC_PORT=$(get_port el-3-geth-lighthouse rpc)

cat > "$REPO_ROOT/observability/.env" <<EOF
EL_METRICS_PORT=${EL_METRICS_PORT}
CL_METRICS_PORT=${CL_METRICS_PORT}
EL_RPC_PORT=${EL_RPC_PORT}
EOF

cd "$REPO_ROOT/observability"
docker compose up -d

echo ""
echo "services:"
echo "  rpc:        http://127.0.0.1:${EL_RPC_PORT}"
echo "  grafana:    http://localhost:3000 (admin/admin)"
echo "  prometheus: http://localhost:9090"
echo ""
echo "teardown:"
echo "  cd $REPO_ROOT/observability && docker compose down"
echo "  kurtosis enclave rm -f $ENCLAVE_NAME"
