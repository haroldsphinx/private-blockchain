#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import pathlib


SVG_WIDTH = 900
SVG_HEIGHT = 320
PADDING_LEFT = 56
PADDING_RIGHT = 20
PADDING_TOP = 20
PADDING_BOTTOM = 40


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text())


def format_number(value: float | int | None) -> str:
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


def svg_polyline_chart(
    *,
    title: str,
    x_values: list[float],
    series: dict[str, list[float | None]],
    x_label: str,
    y_label: str,
) -> str:
    colors = ["#0b7285", "#c92a2a", "#2b8a3e", "#5f3dc4", "#e67700"]
    valid_y = [
        value
        for values in series.values()
        for value in values
        if value is not None
    ]
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
        legend_x = PADDING_LEFT + 12 + index * 130
        legend_y = PADDING_TOP + 12
        parts.append(f"<line x1='{legend_x}' y1='{legend_y}' x2='{legend_x + 18}' y2='{legend_y}' stroke='{color}' stroke-width='2'/>")
        parts.append(f"<text x='{legend_x + 24}' y='{legend_y + 4}' font-size='11' font-family='monospace'>{name}</text>")

    parts.append("</svg>")
    return "\n".join(parts)


def build_latency_chart(test_name: str, rows: list[dict]) -> str:
    return svg_polyline_chart(
        title=f"{test_name} latency profile",
        x_values=[row["rate"] for row in rows],
        series={
            "mean": [row.get("mean") for row in rows],
            "p95": [row.get("p95") for row in rows],
        },
        x_label="requests per second",
        y_label="seconds",
    )


def build_throughput_chart(benchmarks: dict) -> str:
    rows_by_test = {test_name: data["rows"] for test_name, data in benchmarks.items()}
    rate_set = sorted({row["rate"] for rows in rows_by_test.values() for row in rows})
    series = {}
    for test_name, rows in rows_by_test.items():
        rows_by_rate = {row["rate"]: row for row in rows}
        series[test_name] = [rows_by_rate.get(rate, {}).get("throughput") for rate in rate_set]
    return svg_polyline_chart(
        title="throughput profile",
        x_values=rate_set,
        series=series,
        x_label="target requests per second",
        y_label="observed throughput",
    )


def build_liveness_chart(samples_path: pathlib.Path) -> str:
    timestamps = []
    heights = []
    for line in samples_path.read_text().splitlines()[1:]:
        if not line.strip():
            continue
        timestamp, height = line.split(",")
        timestamps.append(float(timestamp))
        heights.append(float(height))
    if timestamps:
        start = timestamps[0]
        timestamps = [timestamp - start for timestamp in timestamps]
    return svg_polyline_chart(
        title="chain progression",
        x_values=timestamps or [0.0],
        series={"block height": heights or [0.0]},
        x_label="seconds since benchmark start",
        y_label="block height",
    )


def build_node_chart(samples_path: pathlib.Path, column: str, title: str, y_label: str) -> str:
    timestamps = []
    values = []
    for line in samples_path.read_text().splitlines()[1:]:
        if not line.strip():
            continue
        parts = line.split(",")
        row = {
            "timestamp": float(parts[0]),
            "cpu_percent": float(parts[1]),
            "mem_used_bytes": float(parts[2]),
            "mem_limit_bytes": float(parts[3]),
            "peer_count": float(parts[4]),
        }
        timestamps.append(row["timestamp"])
        values.append(row[column])
    if timestamps:
        start = timestamps[0]
        timestamps = [timestamp - start for timestamp in timestamps]
    return svg_polyline_chart(
        title=title,
        x_values=timestamps or [0.0],
        series={column: values or [0.0]},
        x_label="seconds since benchmark start",
        y_label=y_label,
    )


def render_html(run_dir: pathlib.Path, metadata: dict, liveness: dict, benchmarks: dict, charts: dict[str, str]) -> str:
    parts = []
    parts.append("<!doctype html>")
    parts.append("<html lang='en'><head><meta charset='utf-8'>")
    parts.append("<meta name='viewport' content='width=device-width, initial-scale=1'>")
    parts.append("<title>Baseline Benchmark Report</title>")
    parts.append(
        "<style>"
        "body{font-family:Georgia,serif;max-width:1100px;margin:40px auto;padding:0 20px;color:#1f2933;line-height:1.5;}"
        "h1,h2,h3{font-family:Menlo,monospace;}"
        "table{border-collapse:collapse;width:100%;margin:16px 0 24px;}"
        "th,td{border:1px solid #d9e2ec;padding:8px 10px;text-align:right;font-family:Menlo,monospace;font-size:13px;}"
        "th:first-child,td:first-child{text-align:left;}"
        ".meta li{margin:4px 0;}"
        ".chart{margin:20px 0 32px;border:1px solid #d9e2ec;padding:12px;background:#fff;}"
        ".note{background:#f8fafc;border-left:4px solid #0b7285;padding:12px 14px;}"
        "</style></head><body>"
    )
    parts.append("<h1>Baseline Benchmark Report</h1>")
    parts.append("<ul class='meta'>")
    parts.append(f"<li><strong>Run directory:</strong> <code>{run_dir}</code></li>")
    parts.append(f"<li><strong>EL client:</strong> <code>{metadata.get('el_client_version')}</code></li>")
    parts.append(f"<li><strong>CL client:</strong> <code>{metadata.get('cl_client_version')}</code></li>")
    parts.append(f"<li><strong>Target RPC URL:</strong> <code>{metadata.get('target_rpc_url')}</code></li>")
    parts.append(f"<li><strong>Request rates:</strong> <code>{metadata.get('request_rates')}</code></li>")
    parts.append(f"<li><strong>Duration per rate:</strong> <code>{metadata.get('benchmark_duration_seconds')}</code> seconds</li>")
    parts.append("</ul>")
    parts.append("<div class='note'>This run captures the pre-upgrade behavior of the deployed RPC node under fixed-rate load.</div>")
    parts.append("<h2>Liveness</h2>")
    parts.append("<ul class='meta'>")
    parts.append(f"<li><strong>Starting block:</strong> <code>{liveness.get('starting_block')}</code></li>")
    parts.append(f"<li><strong>Ending block:</strong> <code>{liveness.get('ending_block')}</code></li>")
    parts.append(f"<li><strong>Block delta during run:</strong> <code>{liveness.get('block_delta')}</code></li>")
    parts.append(f"<li><strong>Average seconds per observed block increase:</strong> <code>{format_number(liveness.get('average_seconds_per_observed_block'))}</code></li>")
    parts.append(f"<li><strong>Stall detected:</strong> <code>{'yes' if liveness.get('stall_detected') else 'no'}</code></li>")
    parts.append("</ul>")
    parts.append(f"<div class='chart'>{charts['liveness']}</div>")
    node_metrics = metadata.get("node_metrics")
    if node_metrics is not None:
        parts.append("<h2>Node Metrics</h2>")
        parts.append("<ul class='meta'>")
        parts.append(f"<li><strong>Average CPU %:</strong> <code>{format_number(node_metrics.get('avg_cpu_percent'))}</code></li>")
        parts.append(f"<li><strong>Peak CPU %:</strong> <code>{format_number(node_metrics.get('peak_cpu_percent'))}</code></li>")
        parts.append(f"<li><strong>Average memory:</strong> <code>{format_bytes(node_metrics.get('avg_mem_used_bytes'))}</code></li>")
        parts.append(f"<li><strong>Peak memory:</strong> <code>{format_bytes(node_metrics.get('peak_mem_used_bytes'))}</code></li>")
        parts.append(f"<li><strong>Start peers:</strong> <code>{format_number(node_metrics.get('start_peer_count'))}</code></li>")
        parts.append(f"<li><strong>End peers:</strong> <code>{format_number(node_metrics.get('end_peer_count'))}</code></li>")
        parts.append(f"<li><strong>Minimum peers:</strong> <code>{format_number(node_metrics.get('min_peer_count'))}</code></li>")
        parts.append("</ul>")
        parts.append(f"<div class='chart'>{charts['node_cpu']}</div>")
        parts.append(f"<div class='chart'>{charts['node_peers']}</div>")
    parts.append("<h2>RPC Metrics</h2>")
    for test_name, benchmark in benchmarks.items():
        parts.append(f"<h3>{test_name}</h3>")
        parts.append("<table><thead><tr><th>Rate</th><th>Mean</th><th>p50</th><th>p95</th><th>Throughput</th><th>Error Rate</th></tr></thead><tbody>")
        for row in benchmark["rows"]:
            parts.append(
                "<tr>"
                f"<td>{row['rate']}</td>"
                f"<td>{format_number(row.get('mean'))}</td>"
                f"<td>{format_number(row.get('p50'))}</td>"
                f"<td>{format_number(row.get('p95'))}</td>"
                f"<td>{format_number(row.get('throughput'))}</td>"
                f"<td>{format_number(row.get('error_rate'))}</td>"
                "</tr>"
            )
        parts.append("</tbody></table>")
        parts.append(f"<div class='chart'>{charts[test_name]}</div>")
    parts.append("<h3>Throughput Across Tests</h3>")
    parts.append(f"<div class='chart'>{charts['throughput']}</div>")
    parts.append("</body></html>")
    return "\n".join(parts) + "\n"


def main() -> None:
    args = parse_args()
    run_dir = pathlib.Path(args.run)
    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata = load_json(run_dir / "metadata.json")
    liveness = load_json(run_dir / "liveness.json")
    node_metrics_path = run_dir / "node_metrics.json"
    node_metrics = load_json(node_metrics_path) if node_metrics_path.exists() else None
    benchmarks = {}
    for benchmark_dir in sorted((run_dir / "benchmarks").iterdir()):
        if benchmark_dir.is_dir():
            benchmarks[benchmark_dir.name] = load_json(benchmark_dir / "metrics.json")

    charts: dict[str, str] = {}
    for test_name, benchmark in benchmarks.items():
        charts[test_name] = build_latency_chart(test_name, benchmark["rows"])
    charts["throughput"] = build_throughput_chart(benchmarks)
    charts["liveness"] = build_liveness_chart(run_dir / "liveness_samples.csv")
    if node_metrics is not None:
        charts["node_cpu"] = build_node_chart(run_dir / "node_metrics_samples.csv", "cpu_percent", "geth CPU usage", "CPU %")
        charts["node_peers"] = build_node_chart(run_dir / "node_metrics_samples.csv", "peer_count", "peer count during benchmark", "peer count")
    metadata["node_metrics"] = node_metrics

    summary = {
        "metadata": metadata,
        "liveness": liveness,
        "benchmarks": benchmarks,
    }
    (output_dir / "results.json").write_text(json.dumps(summary, indent=2) + "\n")
    (output_dir / "report.html").write_text(render_html(run_dir, metadata, liveness, benchmarks, charts))


if __name__ == "__main__":
    main()
