#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "usage: $0 <current|candidate|label> [workload_from_run_dir]" >&2
  exit 1
fi

LABEL="$1"
WORKLOAD_FROM="${2:-${BENCHMARK_WORKLOAD_FROM:-}}"

RPC_URL="${BENCHMARK_RPC_URL:-}"
CL_URL="${BENCHMARK_CL_URL:-}"
RATES="${BENCHMARK_RATES:-25 100 250}"
DURATION="${BENCHMARK_DURATION:-30}"
POLL_INTERVAL="${BENCHMARK_POLL_INTERVAL:-5}"
STALL_THRESHOLD="${BENCHMARK_STALL_THRESHOLD:-60}"
TARGET_NODE_LABEL="${BENCHMARK_TARGET_NODE_LABEL:-node-3}"
FLOOD_PYTHON="${BENCHMARK_PYTHON_BIN:-python3}"
SSH_HOST="${BENCHMARK_SSH_HOST:-}"
SSH_BIN="${BENCHMARK_SSH_BIN:-ssh}"
BENCHMARK_VERBOSE="${BENCHMARK_VERBOSE:-1}"

if [[ -z "$RPC_URL" ]]; then
  echo "BENCHMARK_RPC_URL is required" >&2
  exit 1
fi

if ! command -v vegeta >/dev/null 2>&1; then
  echo "vegeta is required on PATH" >&2
  exit 1
fi

if ! "$FLOOD_PYTHON" -c 'import flood' >/dev/null 2>&1; then
  echo "python flood package is required for benchmark execution" >&2
  exit 1
fi

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="${BENCHMARK_OUTPUT_DIR:-$REPO_ROOT/results/$LABEL/$TIMESTAMP}"
mkdir -p "$RUN_DIR/benchmarks"

WORKLOAD_PATH="$RUN_DIR/workload.json"
LIVENESS_JSON="$RUN_DIR/liveness.json"
LIVENESS_CSV="$RUN_DIR/liveness_samples.csv"
NODE_METRICS_JSON="$RUN_DIR/node_metrics.json"
NODE_METRICS_CSV="$RUN_DIR/node_metrics_samples.csv"
NODE_METRICS_ERRORS="$RUN_DIR/node_metrics_errors.log"

log() {
  printf '[benchmark] %s\n' "$*"
}

cleanup() {
  if [[ -n "${MONITOR_PID:-}" ]]; then
    kill -TERM "$MONITOR_PID" >/dev/null 2>&1 || true
    wait "$MONITOR_PID" >/dev/null 2>&1 || true
  fi
  if [[ -n "${NODE_MONITOR_PID:-}" ]]; then
    kill -TERM "$NODE_MONITOR_PID" >/dev/null 2>&1 || true
    wait "$NODE_MONITOR_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

run_method() {
  local method="$1"
  local output_dir="$RUN_DIR/benchmarks/$method"

  log "running $method"
  if [[ -n "$WORKLOAD_FROM" ]]; then
    "$FLOOD_PYTHON" "$SCRIPT_DIR/flood_rpc_benchmark.py" \
      --rpc-url "$RPC_URL" \
      --method "$method" \
      --label "$LABEL" \
      --rates $RATES \
      --duration "$DURATION" \
      --output-dir "$output_dir" \
      --workload-path "$WORKLOAD_PATH" \
      --verbose "$BENCHMARK_VERBOSE" \
      --workload-from "$WORKLOAD_FROM/workload.json"
  else
    "$FLOOD_PYTHON" "$SCRIPT_DIR/flood_rpc_benchmark.py" \
      --rpc-url "$RPC_URL" \
      --method "$method" \
      --label "$LABEL" \
      --rates $RATES \
      --duration "$DURATION" \
      --output-dir "$output_dir" \
      --workload-path "$WORKLOAD_PATH" \
      --verbose "$BENCHMARK_VERBOSE"
  fi
}

log "output directory: $RUN_DIR"
log "starting liveness monitor"

"$FLOOD_PYTHON" "$SCRIPT_DIR/monitor_liveness.py" \
  --rpc-url "$RPC_URL" \
  --poll-interval "$POLL_INTERVAL" \
  --stall-threshold "$STALL_THRESHOLD" \
  --output-json "$LIVENESS_JSON" \
  --output-csv "$LIVENESS_CSV" &
MONITOR_PID=$!

if [[ -n "$SSH_HOST" ]]; then
  log "starting node monitor"
  "$FLOOD_PYTHON" "$SCRIPT_DIR/monitor_node.py" \
    --ssh-host "$SSH_HOST" \
    --ssh-bin "$SSH_BIN" \
    --poll-interval "$POLL_INTERVAL" \
    --output-json "$NODE_METRICS_JSON" \
    --output-csv "$NODE_METRICS_CSV" \
    --error-log "$NODE_METRICS_ERRORS" &
  NODE_MONITOR_PID=$!
fi

run_method eth_blockNumber
run_method eth_getBlockByNumber

cleanup
unset MONITOR_PID
unset NODE_MONITOR_PID

log "writing metadata"

"$FLOOD_PYTHON" - "$RUN_DIR" "$LABEL" "$RPC_URL" "$CL_URL" "$TARGET_NODE_LABEL" "$DURATION" "$RATES" "$REPO_ROOT" "$SSH_HOST" <<'PY'
import json
import pathlib
import subprocess
import sys
import urllib.request

run_dir = pathlib.Path(sys.argv[1])
label = sys.argv[2]
rpc_url = sys.argv[3]
cl_url = sys.argv[4]
target_node_label = sys.argv[5]
duration = int(sys.argv[6])
rates = sys.argv[7].split()
repo_root = pathlib.Path(sys.argv[8])
ssh_host = sys.argv[9]


def rpc_call(url, method, params=None):
    if params is None:
        params = []
    payload = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    ).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode())


def http_json(url):
    with urllib.request.urlopen(url, timeout=20) as response:
        return json.loads(response.read().decode())


git_sha = subprocess.check_output(
    ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True
).strip()

el_version = None
cl_version = None
try:
    el_version = rpc_call(rpc_url, "web3_clientVersion")["result"]
except Exception:
    pass
if cl_url:
    try:
        cl_version = http_json(cl_url.rstrip("/") + "/eth/v1/node/version")["data"]["version"]
    except Exception:
        pass

metadata = {
    "environment_label": label,
    "git_sha": git_sha,
    "target_rpc_url": rpc_url,
    "target_node_label": target_node_label,
    "cl_beacon_url": cl_url or None,
    "benchmark_duration_seconds": duration,
    "request_rates": [int(rate) for rate in rates],
    "test_names": ["eth_blockNumber", "eth_getBlockByNumber"],
    "el_client_version": el_version,
    "cl_client_version": cl_version,
    "ssh_host": ssh_host if ssh_host else None,
}

(run_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
PY

log "done: $RUN_DIR"
