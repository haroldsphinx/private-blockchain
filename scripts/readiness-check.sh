#!/bin/bash
set -euo pipefail

RPC_URL="${RPC_URL:-http://52.44.40.113:8545}"
SSH_USER="${SSH_USER:-ubuntu}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_ed25519}"
BLOCK_INTERVAL_SECONDS="${BLOCK_INTERVAL_SECONDS:-60}"

VALIDATOR_IPS_STR="${VALIDATOR_IPS:-54.175.18.52 54.221.168.200}"
read -r -a VALIDATOR_IPS <<<"$VALIDATOR_IPS_STR"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "missing required command: $1" >&2
    exit 1
  fi
}

require_cmd curl
require_cmd jq
require_cmd ssh

rpc_call() {
  local method="$1"
  local params="${2:-[]}"
  curl -sS --max-time 10 "$RPC_URL" \
    -H 'Content-Type: application/json' \
    -d "{\"jsonrpc\":\"2.0\",\"method\":\"$method\",\"params\":$params,\"id\":1}"
}

hex_to_dec() {
  local value="$1"
  if [[ ! "$value" =~ ^0x[0-9a-fA-F]+$ ]]; then
    echo "invalid hex value: $value" >&2
    return 1
  fi
  printf '%d\n' "$((value))"
}

check_rpc_reachable() {
  local response
  response="$(rpc_call web3_clientVersion)"
  local version
  version="$(jq -r '.result // empty' <<<"$response")"
  if [[ -z "$version" ]]; then
    echo "RPC reachable: FAIL"
    echo "$response"
    return 1
  fi

  echo "RPC reachable: PASS ($version)"
}

check_peer_count() {
  local response result peer_count
  response="$(rpc_call net_peerCount)"
  result="$(jq -r '.result // empty' <<<"$response")"
  peer_count="$(hex_to_dec "$result")"

  if (( peer_count < 1 )); then
    echo "Peer count: FAIL ($peer_count)"
    return 1
  fi

  echo "Peer count: PASS ($peer_count)"
}

check_block_progression() {
  local first_response second_response first_hex second_hex first_block second_block

  first_response="$(rpc_call eth_blockNumber)"
  first_hex="$(jq -r '.result // empty' <<<"$first_response")"
  first_block="$(hex_to_dec "$first_hex")"

  sleep "$BLOCK_INTERVAL_SECONDS"

  second_response="$(rpc_call eth_blockNumber)"
  second_hex="$(jq -r '.result // empty' <<<"$second_response")"
  second_block="$(hex_to_dec "$second_hex")"

  if (( second_block <= first_block )); then
    echo "Block progression: FAIL ($first_block -> $second_block over ${BLOCK_INTERVAL_SECONDS}s)"
    return 1
  fi

  echo "Block progression: PASS ($first_block -> $second_block over ${BLOCK_INTERVAL_SECONDS}s)"
}

check_sync_status() {
  local response syncing
  response="$(rpc_call eth_syncing)"
  syncing="$(jq -r '.result' <<<"$response")"

  if [[ "$syncing" != "false" ]]; then
    echo "Execution sync status: WARN ($syncing)"
    return 1
  fi

  echo "Execution sync status: PASS (false)"
}

check_validator_host() {
  local ip="$1"
  local ssh_cmd=(ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=10 "$SSH_USER@$ip")
  local bn_sync bn_peers bn_head vc_logs failed=0

  echo "Validator $ip"

  if ! bn_sync="$("${ssh_cmd[@]}" "curl -sS --max-time 5 http://127.0.0.1:5052/eth/v1/node/syncing")"; then
    echo "  Beacon API syncing: FAIL"
    failed=1
  else
    echo "  Beacon API syncing: PASS"
    echo "    $bn_sync"
  fi

  if ! bn_peers="$("${ssh_cmd[@]}" "curl -sS --max-time 5 http://127.0.0.1:5052/eth/v1/node/peer_count")"; then
    echo "  Beacon API peer_count: FAIL"
    failed=1
  else
    echo "  Beacon API peer_count: PASS"
    echo "    $bn_peers"
  fi

  if ! bn_head="$("${ssh_cmd[@]}" "curl -sS --max-time 5 http://127.0.0.1:5052/eth/v1/beacon/headers/head")"; then
    echo "  Beacon API head: FAIL"
    failed=1
  else
    echo "  Beacon API head: PASS"
    echo "    $(jq -c '.' <<<"$bn_head")"
  fi

  if ! vc_logs="$("${ssh_cmd[@]}" "sudo docker logs --tail 50 lighthouse-vc 2>&1")"; then
    echo "  Validator logs: FAIL"
    failed=1
  else
    if grep -Eq 'All validators inactive|No synced beacon nodes|kind: timeout|Offline, endpoint' <<<"$vc_logs"; then
      echo "  Validator logs: FAIL"
      echo "$vc_logs" | tail -20 | sed 's/^/    /'
      failed=1
    else
      echo "  Validator logs: PASS"
    fi
  fi

  return "$failed"
}

main() {
  local failures=0

  check_rpc_reachable || failures=1
  check_peer_count || failures=1
  check_sync_status || failures=1
  check_block_progression || failures=1

  for ip in "${VALIDATOR_IPS[@]}"; do
    check_validator_host "$ip" || failures=1
  done

  if (( failures != 0 )); then
    echo "Readiness: FAIL"
    exit 1
  fi

  echo "Readiness: PASS"
}

main "$@"
