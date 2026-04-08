#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

RUN_DIR="${1:-}"

latest_run_dir() {
  local label_dir="$1"
  if [[ ! -d "$label_dir" ]]; then
    return 1
  fi
  find "$label_dir" -mindepth 1 -maxdepth 1 -type d | sort | tail -n 1
}

if [[ -z "$RUN_DIR" ]]; then
  RUN_DIR="$(latest_run_dir "$REPO_ROOT/results/current")"
fi

if [[ -z "$RUN_DIR" ]]; then
  echo "unable to determine run directory" >&2
  exit 1
fi

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTPUT_DIR="${BENCHMARK_BASELINE_REPORT_DIR:-$REPO_ROOT/reports/baseline-$TIMESTAMP}"
mkdir -p "$OUTPUT_DIR"

python3 "$REPO_ROOT/scripts/report/generate_baseline_report.py" \
  --run "$RUN_DIR" \
  --output-dir "$OUTPUT_DIR"

echo "report written to $OUTPUT_DIR/report.html"
