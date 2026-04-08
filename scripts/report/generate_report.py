#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import pathlib


COMPARISON_METRICS = ["mean", "p50", "p95", "p99", "throughput", "error_rate"]
LOWER_IS_BETTER = {"mean", "p50", "p95", "p99", "error_rate"}
UNCHANGED_RELATIVE_THRESHOLD = 0.02


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text())


def load_run(run_dir: pathlib.Path) -> dict:
    benchmarks = {}
    benchmarks_dir = run_dir / "benchmarks"
    for test_dir in sorted(benchmarks_dir.iterdir()):
        if test_dir.is_dir():
            benchmarks[test_dir.name] = load_json(test_dir / "metrics.json")
    node_metrics_path = run_dir / "node_metrics.json"
    return {
        "metadata": load_json(run_dir / "metadata.json"),
        "liveness": load_json(run_dir / "liveness.json"),
        "benchmarks": benchmarks,
        "node_metrics": load_json(node_metrics_path) if node_metrics_path.exists() else None,
    }


def compute_delta(current: float | None, candidate: float | None) -> float | None:
    if current is None or candidate is None:
        return None
    return candidate - current


def verdict(metric: str, current: float | None, candidate: float | None) -> str:
    if current is None or candidate is None:
        return "n/a"
    delta = candidate - current
    denominator = abs(current) if current != 0 else 1
    if abs(delta) / denominator <= UNCHANGED_RELATIVE_THRESHOLD:
        return "unchanged"
    improved = delta < 0 if metric in LOWER_IS_BETTER else delta > 0
    return "improved" if improved else "regressed"


def format_value(value: float | int | None) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, int):
        return str(value)
    if math.isnan(value):
        return "n/a"
    return f"{value:.4f}"


def format_bytes(value: float | int | None) -> str:
    if value is None:
        return "n/a"
    return f"{float(value) / (1024 * 1024):.2f} MiB"


def build_comparison(current_run: dict, candidate_run: dict) -> dict:
    rows = []
    for test_name, current_test in current_run["benchmarks"].items():
        candidate_test = candidate_run["benchmarks"].get(test_name, {"rows": []})
        candidate_rows = {row["rate"]: row for row in candidate_test["rows"]}
        for current_row in current_test["rows"]:
            candidate_row = candidate_rows.get(current_row["rate"], {})
            for metric in COMPARISON_METRICS:
                current_value = current_row.get(metric)
                candidate_value = candidate_row.get(metric)
                rows.append(
                    {
                        "test_name": test_name,
                        "rate": current_row["rate"],
                        "metric": metric,
                        "current": current_value,
                        "candidate": candidate_value,
                        "delta": compute_delta(current_value, candidate_value),
                        "verdict": verdict(metric, current_value, candidate_value),
                    }
                )
    return {"rows": rows}


def render_markdown(current_dir: pathlib.Path, candidate_dir: pathlib.Path, current_run: dict, candidate_run: dict, comparison: dict) -> str:
    lines = []
    lines.append("# Benchmark Comparison")
    lines.append("")
    lines.append(f"- Current run: `{current_dir}`")
    lines.append(f"- Candidate run: `{candidate_dir}`")
    lines.append(f"- Current EL client: `{current_run['metadata'].get('el_client_version')}`")
    lines.append(f"- Candidate EL client: `{candidate_run['metadata'].get('el_client_version')}`")
    lines.append(f"- Current CL client: `{current_run['metadata'].get('cl_client_version')}`")
    lines.append(f"- Candidate CL client: `{candidate_run['metadata'].get('cl_client_version')}`")
    lines.append("")
    lines.append("## RPC Metrics")
    lines.append("")
    lines.append("| Test | Rate | Metric | Current | Candidate | Delta | Verdict |")
    lines.append("| --- | ---: | --- | ---: | ---: | ---: | --- |")
    for row in comparison["rows"]:
        lines.append(
            "| {test_name} | {rate} | {metric} | {current} | {candidate} | {delta} | {verdict} |".format(
                test_name=row["test_name"],
                rate=row["rate"],
                metric=row["metric"],
                current=format_value(row["current"]),
                candidate=format_value(row["candidate"]),
                delta=format_value(row["delta"]),
                verdict=row["verdict"],
            )
        )
    lines.append("")
    lines.append("## Liveness")
    lines.append("")
    lines.append("| Run | Start Block | End Block | Block Delta | Avg Seconds Per Block Increase | Stall Detected |")
    lines.append("| --- | ---: | ---: | ---: | ---: | --- |")
    for label, run in (("current", current_run), ("candidate", candidate_run)):
        live = run["liveness"]
        lines.append(
            "| {label} | {start} | {end} | {delta} | {avg} | {stall} |".format(
                label=label,
                start=format_value(live.get("starting_block")),
                end=format_value(live.get("ending_block")),
                delta=format_value(live.get("block_delta")),
                avg=format_value(live.get("average_seconds_per_observed_block")),
                stall="yes" if live.get("stall_detected") else "no",
            )
        )
    lines.append("")
    lines.append("## Node Metrics")
    lines.append("")
    lines.append("| Run | Avg CPU % | Peak CPU % | Avg Memory | Peak Memory | Start Peers | End Peers | Min Peers |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for label, run in (("current", current_run), ("candidate", candidate_run)):
        metrics = run.get("node_metrics") or {}
        lines.append(
            "| {label} | {avg_cpu} | {peak_cpu} | {avg_mem} | {peak_mem} | {start_peers} | {end_peers} | {min_peers} |".format(
                label=label,
                avg_cpu=format_value(metrics.get("avg_cpu_percent")),
                peak_cpu=format_value(metrics.get("peak_cpu_percent")),
                avg_mem=format_bytes(metrics.get("avg_mem_used_bytes")),
                peak_mem=format_bytes(metrics.get("peak_mem_used_bytes")),
                start_peers=format_value(metrics.get("start_peer_count")),
                end_peers=format_value(metrics.get("end_peer_count")),
                min_peers=format_value(metrics.get("min_peer_count")),
            )
        )
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    current_dir = pathlib.Path(args.current)
    candidate_dir = pathlib.Path(args.candidate)
    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    current_run = load_run(current_dir)
    candidate_run = load_run(candidate_dir)
    comparison = build_comparison(current_run, candidate_run)

    summary = {
        "current": current_run,
        "candidate": candidate_run,
        "comparison": comparison,
    }
    (output_dir / "results.json").write_text(json.dumps(summary, indent=2) + "\n")
    report_text = render_markdown(current_dir, candidate_dir, current_run, candidate_run, comparison)
    (output_dir / "report.md").write_text(report_text)
    (output_dir / "summary.txt").write_text(report_text)
    (output_dir / "comparison.md").write_text(
        render_markdown(current_dir, candidate_dir, current_run, candidate_run, comparison)
    )


if __name__ == "__main__":
    main()
