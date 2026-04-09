#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib


SMALLER_FILE = "github-action-benchmark-smaller.json"
BIGGER_FILE = "github-action-benchmark-bigger.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text())


def append_rpc_entries(entries: list[dict], benchmark_name: str, metrics: dict, lower_is_better: bool) -> None:
    for row in metrics["rows"]:
        rate = row["rate"]
        if lower_is_better:
            for metric_name in ("mean", "p50", "p95", "error_rate"):
                entries.append(
                    {
                        "name": f"{benchmark_name} @ {rate} rps - {metric_name}",
                        "unit": "seconds" if metric_name != "error_rate" else "ratio",
                        "value": row[metric_name],
                        "extra": f"throughput={row['throughput']:.4f} req/s\nrequests={row['requests']}",
                    }
                )
        else:
            entries.append(
                {
                    "name": f"{benchmark_name} @ {rate} rps - throughput",
                    "unit": "req/s",
                    "value": row["throughput"],
                    "extra": f"mean={row['mean']:.4f}s\np95={row['p95']:.4f}s\nerrors={len(row['errors'])}",
                }
            )


def main() -> None:
    args = parse_args()
    run_dir = pathlib.Path(args.run)
    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    smaller_entries: list[dict] = []
    bigger_entries: list[dict] = []

    for benchmark_dir in sorted((run_dir / "benchmarks").iterdir()):
        if not benchmark_dir.is_dir():
            continue
        metrics = load_json(benchmark_dir / "metrics.json")
        append_rpc_entries(smaller_entries, benchmark_dir.name, metrics, lower_is_better=True)
        append_rpc_entries(bigger_entries, benchmark_dir.name, metrics, lower_is_better=False)

    liveness = load_json(run_dir / "liveness.json")
    bigger_entries.append(
        {
            "name": "chain progression - block delta",
            "unit": "blocks",
            "value": liveness.get("block_delta") or 0,
            "extra": f"start={liveness.get('starting_block')}\nend={liveness.get('ending_block')}\nstall_detected={liveness.get('stall_detected')}",
        }
    )

    avg_block_time = liveness.get("average_seconds_per_observed_block")
    if avg_block_time is not None:
        smaller_entries.append(
            {
                "name": "chain progression - avg seconds per observed block",
                "unit": "seconds",
                "value": avg_block_time,
                "extra": f"block_delta={liveness.get('block_delta')}\nstall_detected={liveness.get('stall_detected')}",
            }
        )

    node_metrics_path = run_dir / "node_metrics.json"
    if node_metrics_path.exists():
        node_metrics = load_json(node_metrics_path)
        if node_metrics.get("avg_cpu_percent") is not None:
            smaller_entries.append(
                {
                    "name": "node metrics - avg cpu percent",
                    "unit": "percent",
                    "value": node_metrics["avg_cpu_percent"],
                    "extra": f"peak_cpu={node_metrics.get('peak_cpu_percent')}\nssh_host={node_metrics.get('ssh_host')}",
                }
            )
        if node_metrics.get("peak_cpu_percent") is not None:
            smaller_entries.append(
                {
                    "name": "node metrics - peak cpu percent",
                    "unit": "percent",
                    "value": node_metrics["peak_cpu_percent"],
                    "extra": f"avg_cpu={node_metrics.get('avg_cpu_percent')}\nssh_host={node_metrics.get('ssh_host')}",
                }
            )
        if node_metrics.get("avg_mem_used_bytes") is not None:
            smaller_entries.append(
                {
                    "name": "node metrics - avg memory used",
                    "unit": "bytes",
                    "value": node_metrics["avg_mem_used_bytes"],
                    "extra": f"peak_mem={node_metrics.get('peak_mem_used_bytes')}\nssh_host={node_metrics.get('ssh_host')}",
                }
            )
        if node_metrics.get("peak_mem_used_bytes") is not None:
            smaller_entries.append(
                {
                    "name": "node metrics - peak memory used",
                    "unit": "bytes",
                    "value": node_metrics["peak_mem_used_bytes"],
                    "extra": f"avg_mem={node_metrics.get('avg_mem_used_bytes')}\nssh_host={node_metrics.get('ssh_host')}",
                }
            )
        if node_metrics.get("min_peer_count") is not None:
            bigger_entries.append(
                {
                    "name": "node metrics - minimum peer count",
                    "unit": "peers",
                    "value": node_metrics["min_peer_count"],
                    "extra": f"start={node_metrics.get('start_peer_count')}\nend={node_metrics.get('end_peer_count')}",
                }
            )

    (output_dir / SMALLER_FILE).write_text(json.dumps(smaller_entries, indent=2) + "\n")
    (output_dir / BIGGER_FILE).write_text(json.dumps(bigger_entries, indent=2) + "\n")


if __name__ == "__main__":
    main()
