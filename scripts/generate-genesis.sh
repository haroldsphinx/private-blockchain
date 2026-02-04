#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
GENESIS_DIR="$REPO_ROOT/genesis"

command -v kurtosis >/dev/null 2>&1 || { echo "kurtosis not installed"; exit 1; }

kurtosis engine start || true
kurtosis enclave rm -f genesis-gen 2>/dev/null || true

kurtosis run --enclave genesis-gen \
  github.com/ethpandaops/ethereum-package \
  --args-file "$REPO_ROOT/kurtosis/network_params_genesis.yaml"

rm -rf "$GENESIS_DIR/el" "$GENESIS_DIR/cl" "$GENESIS_DIR/validator-keys"
mkdir -p "$GENESIS_DIR/el" "$GENESIS_DIR/cl" "$GENESIS_DIR/validator-keys/node-1" "$GENESIS_DIR/validator-keys/node-2" "$GENESIS_DIR/nodekeys"

TEMP_DIR=$(mktemp -d)
kurtosis files download genesis-gen el_cl_genesis_data "$TEMP_DIR/genesis"
kurtosis files download genesis-gen validator_keys "$TEMP_DIR/keys"

cp "$TEMP_DIR/genesis/genesis.json" "$GENESIS_DIR/el/"
cp "$TEMP_DIR/genesis/config.yaml" "$GENESIS_DIR/cl/"
cp "$TEMP_DIR/genesis/genesis.ssz" "$GENESIS_DIR/cl/"

# Split keys between nodes
KEY_DIRS=($(ls -d "$TEMP_DIR/keys/keys"/0x* 2>/dev/null | sort))
HALF=$((${#KEY_DIRS[@]} / 2))

for i in $(seq 0 $((HALF - 1))); do
  cp -r "${KEY_DIRS[$i]}" "$GENESIS_DIR/validator-keys/node-1/keys/"
done
for i in $(seq $HALF $((${#KEY_DIRS[@]} - 1))); do
  cp -r "${KEY_DIRS[$i]}" "$GENESIS_DIR/validator-keys/node-2/keys/"
done
cp -r "$TEMP_DIR/keys/secrets" "$GENESIS_DIR/validator-keys/node-1/"
cp -r "$TEMP_DIR/keys/secrets" "$GENESIS_DIR/validator-keys/node-2/"

# Generate deterministic nodekeys
for node in node-1 node-2 node-3; do
  openssl rand -hex 32 > "$GENESIS_DIR/nodekeys/$node.key"
done
openssl rand -hex 32 > "$GENESIS_DIR/jwt.hex"

rm -rf "$TEMP_DIR"
kurtosis enclave rm -f genesis-gen

echo "Genesis files generated in $GENESIS_DIR"
