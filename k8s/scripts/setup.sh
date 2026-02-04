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

# extract ports for the observability docker-compose stack
get_port() {
  kurtosis service inspect "$ENCLAVE_NAME" "$1" | grep "$2:" | sed -n 's/.*-> [0-9.]*:\([0-9]*\).*/\1/p' | head -1
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
echo "all kurtosis ports bound to 0.0.0.0 via port_publisher:"
kurtosis enclave inspect "$ENCLAVE_NAME"
echo ""
echo "observability stack:"
echo "  grafana:    http://localhost:3001 (admin/admin)"
echo "  prometheus: http://localhost:9091"
echo "  alertmanager: http://localhost:9093"
echo ""
echo "teardown:"
echo "  cd $REPO_ROOT/observability && docker compose down"
echo "  kurtosis enclave rm -f $ENCLAVE_NAME"
