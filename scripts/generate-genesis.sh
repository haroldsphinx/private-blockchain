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
  --args-file "$REPO_ROOT/kurtosis/network_params.yaml"

rm -rf "$GENESIS_DIR/el" "$GENESIS_DIR/cl" "$GENESIS_DIR/validator-keys"
mkdir -p "$GENESIS_DIR/el" "$GENESIS_DIR/cl" "$GENESIS_DIR/validator-keys/node-1/keys" "$GENESIS_DIR/validator-keys/node-2/keys" "$GENESIS_DIR/nodekeys"

TEMP_DIR=$(mktemp -d)
kurtosis files download genesis-gen el_cl_genesis_data "$TEMP_DIR/genesis"
kurtosis files download genesis-gen 1-lighthouse-geth-0-31 "$TEMP_DIR/keys-node-1"
kurtosis files download genesis-gen 2-lighthouse-geth-32-63 "$TEMP_DIR/keys-node-2"

cp "$TEMP_DIR/genesis/genesis.json" "$GENESIS_DIR/el/"
cp "$TEMP_DIR/genesis/config.yaml" "$GENESIS_DIR/cl/"
cp "$TEMP_DIR/genesis/genesis.ssz" "$GENESIS_DIR/cl/"

# Create required Lighthouse files for custom testnet
echo "0" > "$GENESIS_DIR/cl/deposit_contract_block.txt"
echo "0" > "$GENESIS_DIR/cl/deploy_block.txt"

# Copy validator keys (already split by Kurtosis)
cp -r "$TEMP_DIR/keys-node-1/keys/"* "$GENESIS_DIR/validator-keys/node-1/keys/"
cp -r "$TEMP_DIR/keys-node-1/secrets" "$GENESIS_DIR/validator-keys/node-1/"
cp -r "$TEMP_DIR/keys-node-2/keys/"* "$GENESIS_DIR/validator-keys/node-2/keys/"
cp -r "$TEMP_DIR/keys-node-2/secrets" "$GENESIS_DIR/validator-keys/node-2/"

# Generate deterministic nodekeys
for node in node-1 node-2 node-3; do
  openssl rand -hex 32 > "$GENESIS_DIR/nodekeys/$node.key"
done
openssl rand -hex 32 > "$GENESIS_DIR/jwt.hex"

rm -rf "$TEMP_DIR"
kurtosis enclave rm -f genesis-gen

echo "Genesis files generated in $GENESIS_DIR"
