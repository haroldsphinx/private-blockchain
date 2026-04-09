#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import pathlib
import shutil
import subprocess
import tempfile


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--branch", default="gh-pages")
    parser.add_argument("--token-env", default="BENCHMARK_PAGES_TOKEN")
    parser.add_argument("--baseline-report-dir")
    parser.add_argument("--comparison-report-dir")
    parser.add_argument("--comparison-label")
    return parser.parse_args()


def run(cmd: list[str], cwd: pathlib.Path | None = None) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def render_index(pages_dir: pathlib.Path) -> str:
    baseline_root = pages_dir / "benchmarks" / "baseline"
    comparison_root = pages_dir / "benchmarks" / "comparisons"
    baseline_reports = sorted(
        [p for p in baseline_root.iterdir() if p.is_dir() and p.name != "latest"],
        reverse=True,
    ) if baseline_root.exists() else []
    comparison_reports = sorted(
        [p for p in comparison_root.iterdir() if p.is_dir()],
        reverse=True,
    ) if comparison_root.exists() else []

    lines = [
        "<!doctype html>",
        "<html lang='en'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<title>Benchmark Reports</title>",
        "<style>"
        "body{font-family:Georgia,serif;max-width:980px;margin:40px auto;padding:0 20px;color:#1f2933;line-height:1.5;}"
        "h1,h2{font-family:Menlo,monospace;}"
        "a{color:#0b7285;text-decoration:none;}"
        "a:hover{text-decoration:underline;}"
        "code{font-family:Menlo,monospace;background:#f8fafc;padding:2px 4px;}"
        "li{margin:8px 0;}"
        ".muted{color:#52606d;}"
        "</style></head><body>",
        "<h1>Benchmark Reports</h1>",
        "<p class='muted'>Published from GitHub Actions.</p>",
        "<h2>Baseline</h2>",
    ]

    latest = baseline_root / "latest" / "report.html"
    if latest.exists():
        lines.append("<p><a href='benchmarks/baseline/latest/report.html'>Open latest baseline report</a></p>")
    else:
        lines.append("<p class='muted'>No baseline report published yet.</p>")

    if baseline_reports:
        lines.append("<ul>")
        for report_dir in baseline_reports[:20]:
            lines.append(
                f"<li><a href='benchmarks/baseline/{report_dir.name}/report.html'>{report_dir.name}</a></li>"
            )
        lines.append("</ul>")

    lines.append("<h2>Comparisons</h2>")
    if comparison_reports:
        lines.append("<ul>")
        for report_dir in comparison_reports[:20]:
            lines.append(
                f"<li><a href='benchmarks/comparisons/{report_dir.name}/report.html'>{report_dir.name}</a></li>"
            )
        lines.append("</ul>")
    else:
        lines.append("<p class='muted'>No comparison reports published yet.</p>")

    lines.append("</body></html>")
    return "\n".join(lines) + "\n"


def render_markdown_html(markdown_text: str, title: str) -> str:
    return "\n".join(
        [
            "<!doctype html>",
            "<html lang='en'><head><meta charset='utf-8'>",
            "<meta name='viewport' content='width=device-width, initial-scale=1'>",
            f"<title>{html.escape(title)}</title>",
            "<style>"
            "body{font-family:Georgia,serif;max-width:1100px;margin:40px auto;padding:0 20px;color:#1f2933;line-height:1.5;}"
            "h1{font-family:Menlo,monospace;}"
            "pre{white-space:pre-wrap;word-break:break-word;background:#f8fafc;border:1px solid #d9e2ec;padding:16px;font-family:Menlo,monospace;font-size:13px;}"
            "a{color:#0b7285;text-decoration:none;}"
            "</style></head><body>",
            f"<h1>{html.escape(title)}</h1>",
            "<p><a href='report.md'>Open raw Markdown</a> | <a href='results.json'>Open results.json</a></p>",
            f"<pre>{html.escape(markdown_text)}</pre>",
            "</body></html>",
        ]
    ) + "\n"


def copy_baseline(report_dir: pathlib.Path, pages_dir: pathlib.Path) -> None:
    report_name = report_dir.name
    archive_dir = pages_dir / "benchmarks" / "baseline" / report_name
    latest_dir = pages_dir / "benchmarks" / "baseline" / "latest"
    archive_dir.mkdir(parents=True, exist_ok=True)
    latest_dir.mkdir(parents=True, exist_ok=True)
    for target_dir in (archive_dir, latest_dir):
        shutil.copy2(report_dir / "report.html", target_dir / "report.html")
        shutil.copy2(report_dir / "results.json", target_dir / "results.json")


def copy_comparison(report_dir: pathlib.Path, pages_dir: pathlib.Path, label: str) -> None:
    target_dir = pages_dir / "benchmarks" / "comparisons" / label
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(report_dir / "report.md", target_dir / "report.md")
    shutil.copy2(report_dir / "results.json", target_dir / "results.json")
    markdown_text = (report_dir / "report.md").read_text()
    (target_dir / "report.html").write_text(render_markdown_html(markdown_text, f"Benchmark Comparison: {label}"))


def main() -> None:
    args = parse_args()
    token = os.environ.get(args.token_env)
    if not token:
        raise SystemExit(f"{args.token_env} is required")

    baseline_report_dir = pathlib.Path(args.baseline_report_dir) if args.baseline_report_dir else None
    comparison_report_dir = pathlib.Path(args.comparison_report_dir) if args.comparison_report_dir else None

    if not baseline_report_dir and not comparison_report_dir:
        raise SystemExit("one of --baseline-report-dir or --comparison-report-dir is required")

    with tempfile.TemporaryDirectory(prefix="gh-pages-publish-") as tmp:
        work_dir = pathlib.Path(tmp)
        remote = f"https://x-access-token:{token}@github.com/{args.repo}.git"
        run(["git", "clone", "--branch", args.branch, remote, str(work_dir)])

        if baseline_report_dir:
            copy_baseline(baseline_report_dir, work_dir)
        if comparison_report_dir:
            label = args.comparison_label or dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            copy_comparison(comparison_report_dir, work_dir, label)

        (work_dir / "index.html").write_text(render_index(work_dir))

        status = subprocess.check_output(["git", "status", "--porcelain"], cwd=work_dir, text=True).strip()
        if not status:
            print("no gh-pages changes to publish")
            return

        run(["git", "config", "user.name", "github-actions[bot]"], cwd=work_dir)
        run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"], cwd=work_dir)
        run(["git", "add", "."], cwd=work_dir)
        run(["git", "commit", "-m", "Publish benchmark reports"], cwd=work_dir)
        run(["git", "push", "origin", args.branch], cwd=work_dir)


if __name__ == "__main__":
    main()
