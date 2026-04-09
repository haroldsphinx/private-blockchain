# Benchmarking

This benchmark flow benchmarks the deployed RPC node, records chain progression during the run, and compares a `current` run against a `candidate` run.

In CI, `baseline` means the most recent benchmark artifact produced from `main`. A manual workflow run benchmarks a requested tag or ref against that saved baseline using the same hardcoded deployed endpoints.

## Scope

- `eth_blockNumber` benchmarked for latency and throughput
- `eth_getBlockByNumber` benchmarked for latency and throughput
- block height progression during the benchmark window
- optional `geth` CPU, memory, and peer count sampling over SSH
- side-by-side current vs candidate comparison report

## Requirements

- `python3`
- `vegeta`
- Python `flood` package available to `python3`

## Required Environment Variables

- `BENCHMARK_RPC_URL`: RPC endpoint to benchmark
- `BENCHMARK_CL_URL`: beacon API endpoint for CL version metadata

## Optional Environment Variables

- `BENCHMARK_RATES`: space-separated request rates, default `25 100 250`
- `BENCHMARK_DURATION`: per-rate duration in seconds, default `30`
- `BENCHMARK_POLL_INTERVAL`: liveness poll interval in seconds, default `5`
- `BENCHMARK_STALL_THRESHOLD`: liveness stall threshold in seconds, default `60`
- `BENCHMARK_TARGET_NODE_LABEL`: metadata label for the RPC target, default `node-3`
- `BENCHMARK_OUTPUT_DIR`: explicit run output directory
- `BENCHMARK_WORKLOAD_FROM`: previous run directory whose workload should be reused exactly
- `BENCHMARK_SSH_HOST`: optional SSH host for node-side `geth` CPU/memory and peer sampling
- `BENCHMARK_SSH_BIN`: optional SSH binary, default `ssh`

## Example

Current run:

```sh
export BENCHMARK_RPC_URL="http://52.44.40.113:8545"
export BENCHMARK_CL_URL="http://54.175.18.52:5052"
export BENCHMARK_SSH_HOST="ubuntu@52.44.40.113"
./scripts/benchmark/run.sh current
```

Candidate run reusing the exact same workload:

```sh
export BENCHMARK_RPC_URL="http://<candidate-rpc>:8545"
export BENCHMARK_CL_URL="http://<candidate-cl>:5052"
./scripts/benchmark/run.sh candidate results/current/<timestamp>
```

Compare the latest `current` and `candidate` runs:

```sh
./scripts/benchmark/compare.sh
```

Create a baseline report with simple charts for a single run:

```sh
./scripts/benchmark/report.sh results/current/<timestamp>
```

Compare specific runs:

```sh
./scripts/benchmark/compare.sh results/current/<timestamp> results/candidate/<timestamp>
```

## CI Model

- every push to `main` produces and uploads a new baseline artifact
- manual workflow runs accept only a `tag` or git ref input
- the manual run benchmarks that ref against the latest saved `main` baseline
- the workflow uses hardcoded deployed RPC, CL, and SSH targets for simplicity
- baseline and comparison reports are also published directly to `gh-pages`
- the Pages site keeps:
  - the latest baseline at `benchmarks/baseline/latest/`
  - archived baseline reports under `benchmarks/baseline/<timestamp>/`
  - comparison reports under `benchmarks/comparisons/<tag-or-ref>/`

## Result Layout

Each run is stored under `results/<label>/<timestamp>/` and includes:

- `metadata.json`
- `workload.json`
- `liveness.json`
- `liveness_samples.csv`
- `node_metrics.json` when `BENCHMARK_SSH_HOST` is set
- `node_metrics_samples.csv` when `BENCHMARK_SSH_HOST` is set
- `benchmarks/eth_blockNumber/`
- `benchmarks/eth_getBlockByNumber/`

Each benchmark directory includes:

- `results.json`: raw Flood-style results
- `test.json`: test metadata for that method
- `metrics.json`: extracted summary used by report generation

Comparison output is written under `reports/<timestamp>/`:

- `report.md`
- `results.json`

Baseline report output is written under `reports/baseline-<timestamp>/`:

- `report.html`
- `results.json`

## Notes

- Flood 0.3.1 does not ship a built-in `eth_blockNumber` test generator, so this repo uses Flood's own load-test runner and result format through a thin Python wrapper for that method.
- `eth_getBlockByNumber` uses block numbers sampled from the live chain head of the baseline run and stores them in `workload.json`, so the candidate run can reuse the exact same request set.
