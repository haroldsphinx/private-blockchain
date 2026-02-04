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

cat > "$REPO_ROOT/observability/.env" <<EOF
EL_METRICS_PORT=32002
CL_METRICS_PORT=33002
EL_RPC_PORT=32017
EOF

cd "$REPO_ROOT/observability"
docker compose up -d
