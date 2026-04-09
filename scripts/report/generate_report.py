#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import pathlib


COMPARISON_METRICS = ["mean", "p50", "p95", "throughput", "error_rate"]
LOWER_IS_BETTER = {"mean", "p50", "p95", "error_rate"}
UNCHANGED_RELATIVE_THRESHOLD = 0.02

SVG_WIDTH = 900
SVG_HEIGHT = 320
PADDING_LEFT = 56
PADDING_RIGHT = 20
PADDING_TOP = 20
PADDING_BOTTOM = 40


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


def compute_relative_delta(current: float | None, candidate: float | None) -> float | None:
    if current is None or candidate is None or current == 0:
        return None
    return ((candidate - current) / current) * 100.0


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


def format_percent(value: float | None) -> str:
    if value is None:
        return "n/a"
    if math.isnan(value):
        return "n/a"
    return f"{value:.2f}%"


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
                        "relative_delta_percent": compute_relative_delta(current_value, candidate_value),
                        "verdict": verdict(metric, current_value, candidate_value),
                    }
                )
    return {"rows": rows}


def svg_polyline_chart(
    *,
    title: str,
    x_values: list[float],
    series: dict[str, list[float | None]],
    x_label: str,
    y_label: str,
) -> str:
    colors = ["#0b7285", "#c92a2a", "#2b8a3e", "#5f3dc4", "#e67700", "#495057"]
    valid_y = [value for values in series.values() for value in values if value is not None]
    if not x_values or not valid_y:
        return (
            f"<svg xmlns='http://www.w3.org/2000/svg' width='{SVG_WIDTH}' height='{SVG_HEIGHT}'>"
            f"<text x='20' y='40'>{title}: no data</text></svg>"
        )

    x_min = min(x_values)
    x_max = max(x_values)
    y_min = min(valid_y)
    y_max = max(valid_y)
    if x_min == x_max:
        x_max = x_min + 1
    if y_min == y_max:
        y_max = y_min + 1

    plot_width = SVG_WIDTH - PADDING_LEFT - PADDING_RIGHT
    plot_height = SVG_HEIGHT - PADDING_TOP - PADDING_BOTTOM

    def map_x(value: float) -> float:
        return PADDING_LEFT + ((value - x_min) / (x_max - x_min)) * plot_width

    def map_y(value: float) -> float:
        return PADDING_TOP + plot_height - ((value - y_min) / (y_max - y_min)) * plot_height

    parts = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{SVG_WIDTH}' height='{SVG_HEIGHT}' viewBox='0 0 {SVG_WIDTH} {SVG_HEIGHT}'>",
        "<rect width='100%' height='100%' fill='white'/>",
        f"<text x='{PADDING_LEFT}' y='16' font-size='16' font-family='monospace'>{title}</text>",
        f"<line x1='{PADDING_LEFT}' y1='{PADDING_TOP + plot_height}' x2='{PADDING_LEFT + plot_width}' y2='{PADDING_TOP + plot_height}' stroke='#333'/>",
        f"<line x1='{PADDING_LEFT}' y1='{PADDING_TOP}' x2='{PADDING_LEFT}' y2='{PADDING_TOP + plot_height}' stroke='#333'/>",
        f"<text x='{SVG_WIDTH / 2}' y='{SVG_HEIGHT - 8}' text-anchor='middle' font-size='12' font-family='monospace'>{x_label}</text>",
        f"<text x='16' y='{SVG_HEIGHT / 2}' transform='rotate(-90 16 {SVG_HEIGHT / 2})' text-anchor='middle' font-size='12' font-family='monospace'>{y_label}</text>",
    ]

    for tick_index in range(5):
        x_tick = x_min + (x_max - x_min) * tick_index / 4
        y_tick = y_min + (y_max - y_min) * tick_index / 4
        x_px = map_x(x_tick)
        y_px = map_y(y_tick)
        parts.append(f"<line x1='{x_px:.2f}' y1='{PADDING_TOP + plot_height}' x2='{x_px:.2f}' y2='{PADDING_TOP + plot_height + 4}' stroke='#666'/>")
        parts.append(f"<text x='{x_px:.2f}' y='{PADDING_TOP + plot_height + 18}' text-anchor='middle' font-size='11' font-family='monospace'>{x_tick:.0f}</text>")
        parts.append(f"<line x1='{PADDING_LEFT - 4}' y1='{y_px:.2f}' x2='{PADDING_LEFT}' y2='{y_px:.2f}' stroke='#666'/>")
        parts.append(f"<text x='{PADDING_LEFT - 8}' y='{y_px + 4:.2f}' text-anchor='end' font-size='11' font-family='monospace'>{y_tick:.2f}</text>")

    for index, (name, values) in enumerate(series.items()):
        color = colors[index % len(colors)]
        points = []
        for x_value, y_value in zip(x_values, values):
            if y_value is None:
                continue
            points.append(f"{map_x(x_value):.2f},{map_y(y_value):.2f}")
        if points:
            parts.append(f"<polyline fill='none' stroke='{color}' stroke-width='2' points='{' '.join(points)}'/>")
        legend_x = PADDING_LEFT + 12 + (index % 3) * 260
        legend_y = PADDING_TOP + 12 + (index // 3) * 16
        parts.append(f"<line x1='{legend_x}' y1='{legend_y}' x2='{legend_x + 18}' y2='{legend_y}' stroke='{color}' stroke-width='2'/>")
        parts.append(f"<text x='{legend_x + 24}' y='{legend_y + 4}' font-size='11' font-family='monospace'>{name}</text>")

    parts.append("</svg>")
    return "\n".join(parts)


def build_metric_chart(test_name: str, current_rows: list[dict], candidate_rows: list[dict], metric: str) -> str:
    current_by_rate = {row["rate"]: row for row in current_rows}
    candidate_by_rate = {row["rate"]: row for row in candidate_rows}
    rates = sorted(set(current_by_rate) | set(candidate_by_rate))
    return svg_polyline_chart(
        title=f"{test_name} {metric}: current vs candidate",
        x_values=rates,
        series={
            "current": [current_by_rate.get(rate, {}).get(metric) for rate in rates],
            "candidate": [candidate_by_rate.get(rate, {}).get(metric) for rate in rates],
        },
        x_label="requests per second",
        y_label="seconds" if metric != "throughput" else "req/s",
    )


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
    lines.append("| Test | Rate | Metric | Current | Candidate | Delta | % Delta | Verdict |")
    lines.append("| --- | ---: | --- | ---: | ---: | ---: | ---: | --- |")
    for row in comparison["rows"]:
        lines.append(
            "| {test_name} | {rate} | {metric} | {current} | {candidate} | {delta} | {relative_delta} | {verdict} |".format(
                test_name=row["test_name"],
                rate=row["rate"],
                metric=row["metric"],
                current=format_value(row["current"]),
                candidate=format_value(row["candidate"]),
                delta=format_value(row["delta"]),
                relative_delta=format_percent(row["relative_delta_percent"]),
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


def render_html(current_dir: pathlib.Path, candidate_dir: pathlib.Path, current_run: dict, candidate_run: dict, comparison: dict, charts: dict[str, str]) -> str:
    parts = [
        "<!doctype html>",
        "<html lang='en'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<title>Benchmark Comparison</title>",
        "<style>"
        "body{font-family:Georgia,serif;max-width:1100px;margin:40px auto;padding:0 20px;color:#1f2933;line-height:1.5;}"
        "h1,h2,h3{font-family:Menlo,monospace;}"
        "table{border-collapse:collapse;width:100%;margin:16px 0 24px;}"
        "th,td{border:1px solid #d9e2ec;padding:8px 10px;text-align:right;font-family:Menlo,monospace;font-size:13px;}"
        "th:first-child,td:first-child{text-align:left;}"
        ".meta li{margin:4px 0;}"
        ".chart{margin:20px 0 32px;border:1px solid #d9e2ec;padding:12px;background:#fff;}"
        ".note{background:#f8fafc;border-left:4px solid #0b7285;padding:12px 14px;}"
        "</style></head><body>",
        "<h1>Benchmark Comparison</h1>",
        "<ul class='meta'>",
        f"<li><strong>Current run:</strong> <code>{current_dir}</code></li>",
        f"<li><strong>Candidate run:</strong> <code>{candidate_dir}</code></li>",
        f"<li><strong>Current EL client:</strong> <code>{current_run['metadata'].get('el_client_version')}</code></li>",
        f"<li><strong>Candidate EL client:</strong> <code>{candidate_run['metadata'].get('el_client_version')}</code></li>",
        f"<li><strong>Current CL client:</strong> <code>{current_run['metadata'].get('cl_client_version')}</code></li>",
        f"<li><strong>Candidate CL client:</strong> <code>{candidate_run['metadata'].get('cl_client_version')}</code></li>",
        "</ul>",
        "<div class='note'>Charts below compare the current baseline against the candidate run using the same saved workload.</div>",
        "<h2>Side-By-Side Charts</h2>",
    ]

    for chart_name in sorted(charts):
        parts.append(f"<div class='chart'>{charts[chart_name]}</div>")

    parts.append("<h2>RPC Metrics</h2>")
    parts.append("<table><thead><tr><th>Test</th><th>Rate</th><th>Metric</th><th>Current</th><th>Candidate</th><th>Delta</th><th>% Delta</th><th>Verdict</th></tr></thead><tbody>")
    for row in comparison["rows"]:
        parts.append(
            "<tr>"
            f"<td>{row['test_name']}</td>"
            f"<td>{row['rate']}</td>"
            f"<td>{row['metric']}</td>"
            f"<td>{format_value(row['current'])}</td>"
            f"<td>{format_value(row['candidate'])}</td>"
            f"<td>{format_value(row['delta'])}</td>"
            f"<td>{format_percent(row['relative_delta_percent'])}</td>"
            f"<td>{row['verdict']}</td>"
            "</tr>"
        )
    parts.append("</tbody></table>")

    parts.append("<h2>Liveness</h2>")
    parts.append("<table><thead><tr><th>Run</th><th>Start Block</th><th>End Block</th><th>Block Delta</th><th>Avg Seconds Per Block Increase</th><th>Stall Detected</th></tr></thead><tbody>")
    for label, run in (("current", current_run), ("candidate", candidate_run)):
        live = run["liveness"]
        parts.append(
            "<tr>"
            f"<td>{label}</td>"
            f"<td>{format_value(live.get('starting_block'))}</td>"
            f"<td>{format_value(live.get('ending_block'))}</td>"
            f"<td>{format_value(live.get('block_delta'))}</td>"
            f"<td>{format_value(live.get('average_seconds_per_observed_block'))}</td>"
            f"<td>{'yes' if live.get('stall_detected') else 'no'}</td>"
            "</tr>"
        )
    parts.append("</tbody></table>")

    parts.append("<h2>Node Metrics</h2>")
    parts.append("<table><thead><tr><th>Run</th><th>Avg CPU %</th><th>Peak CPU %</th><th>Avg Memory</th><th>Peak Memory</th><th>Start Peers</th><th>End Peers</th><th>Min Peers</th></tr></thead><tbody>")
    for label, run in (("current", current_run), ("candidate", candidate_run)):
        metrics = run.get("node_metrics") or {}
        parts.append(
            "<tr>"
            f"<td>{label}</td>"
            f"<td>{format_value(metrics.get('avg_cpu_percent'))}</td>"
            f"<td>{format_value(metrics.get('peak_cpu_percent'))}</td>"
            f"<td>{format_bytes(metrics.get('avg_mem_used_bytes'))}</td>"
            f"<td>{format_bytes(metrics.get('peak_mem_used_bytes'))}</td>"
            f"<td>{format_value(metrics.get('start_peer_count'))}</td>"
            f"<td>{format_value(metrics.get('end_peer_count'))}</td>"
            f"<td>{format_value(metrics.get('min_peer_count'))}</td>"
            "</tr>"
        )
    parts.append("</tbody></table>")
    parts.append("</body></html>")
    return "\n".join(parts) + "\n"


def main() -> None:
    args = parse_args()
    current_dir = pathlib.Path(args.current)
    candidate_dir = pathlib.Path(args.candidate)
    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    current_run = load_run(current_dir)
    candidate_run = load_run(candidate_dir)
    comparison = build_comparison(current_run, candidate_run)

    charts = {}
    all_tests = sorted(set(current_run["benchmarks"]) | set(candidate_run["benchmarks"]))
    for test_name in all_tests:
        current_rows = current_run["benchmarks"].get(test_name, {}).get("rows", [])
        candidate_rows = candidate_run["benchmarks"].get(test_name, {}).get("rows", [])
        charts[f"{test_name}_latency"] = build_metric_chart(test_name, current_rows, candidate_rows, "p95")
        charts[f"{test_name}_throughput"] = build_metric_chart(test_name, current_rows, candidate_rows, "throughput")

    summary = {
        "current": current_run,
        "candidate": candidate_run,
        "comparison": comparison,
    }
    (output_dir / "results.json").write_text(json.dumps(summary, indent=2) + "\n")
    report_text = render_markdown(current_dir, candidate_dir, current_run, candidate_run, comparison)
    (output_dir / "report.md").write_text(report_text)
    (output_dir / "report.html").write_text(
        render_html(current_dir, candidate_dir, current_run, candidate_run, comparison, charts)
    )


if __name__ == "__main__":
    main()
