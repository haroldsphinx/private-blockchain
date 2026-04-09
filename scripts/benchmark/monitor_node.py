#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import pathlib
import shlex
import signal
import subprocess
import sys
import time


RUNNING = True


def handle_signal(signum, frame):  # type: ignore[no-untyped-def]
    global RUNNING
    RUNNING = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ssh-host", required=True)
    parser.add_argument("--ssh-bin", default="ssh")
    parser.add_argument("--poll-interval", type=int, default=5)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-csv", required=True)
    parser.add_argument("--error-log")
    return parser.parse_args()


def ssh_run(ssh_bin: str, host: str, command: str) -> str:
    ssh_argv = [os.path.expanduser(part) for part in shlex.split(ssh_bin)]
    result = subprocess.run(
        [*ssh_argv, host, command],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def write_error_log(path: str | None, message: str) -> None:
    if not path:
        return
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as handle:
        handle.write(message.rstrip() + "\n")


def parse_mem_usage(mem_usage: str) -> tuple[float | None, float | None]:
    try:
        used, limit = [part.strip() for part in mem_usage.split("/", 1)]
        return convert_to_bytes(used), convert_to_bytes(limit)
    except Exception:
        return None, None


def convert_to_bytes(value: str) -> float:
    normalized = value.replace("iB", "B").replace(" ", "")
    units = [
        ("TB", 1000**4),
        ("GB", 1000**3),
        ("MB", 1000**2),
        ("kB", 1000),
        ("B", 1),
    ]
    for unit, multiplier in units:
        if normalized.endswith(unit):
            return float(normalized[: -len(unit)]) * multiplier
    return float(normalized)


def poll_sample(args: argparse.Namespace) -> dict[str, float | int]:
    stats_command = """sudo docker stats geth --no-stream --format '{{.CPUPerc}},{{.MemUsage}}'"""
    rpc_command = """curl -s http://127.0.0.1:8545 -X POST -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","method":"net_peerCount","params":[],"id":1}'"""
    stats_output = ssh_run(args.ssh_bin, args.ssh_host, stats_command)
    rpc_output = ssh_run(args.ssh_bin, args.ssh_host, rpc_command)

    cpu_raw, mem_raw = stats_output.split(",", 1)
    cpu_percent = float(cpu_raw.strip().rstrip("%"))
    mem_used_bytes, mem_limit_bytes = parse_mem_usage(mem_raw)
    rpc_payload = json.loads(rpc_output)
    peer_count = int(rpc_payload["result"], 16)

    return {
        "timestamp": time.time(),
        "cpu_percent": cpu_percent,
        "mem_used_bytes": mem_used_bytes if mem_used_bytes is not None else -1,
        "mem_limit_bytes": mem_limit_bytes if mem_limit_bytes is not None else -1,
        "peer_count": peer_count,
    }


def average(values: list[float]) -> float | None:
    return (sum(values) / len(values)) if values else None


def main() -> None:
    args = parse_args()
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    samples: list[dict[str, float | int]] = []
    failures = 0
    while RUNNING:
        try:
            samples.append(poll_sample(args))
        except Exception as exc:
            failures += 1
            write_error_log(args.error_log, f"{time.time():.0f}: {exc}")
        time.sleep(args.poll_interval)

    with open(args.output_csv, "w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "timestamp",
                "cpu_percent",
                "mem_used_bytes",
                "mem_limit_bytes",
                "peer_count",
            ],
        )
        writer.writeheader()
        writer.writerows(samples)

    cpu_values = [float(sample["cpu_percent"]) for sample in samples]
    mem_used_values = [float(sample["mem_used_bytes"]) for sample in samples if float(sample["mem_used_bytes"]) >= 0]
    peer_values = [int(sample["peer_count"]) for sample in samples]

    summary = {
        "ssh_host": args.ssh_host,
        "samples": len(samples),
        "failed_samples": failures,
        "avg_cpu_percent": average(cpu_values),
        "peak_cpu_percent": max(cpu_values) if cpu_values else None,
        "avg_mem_used_bytes": average(mem_used_values),
        "peak_mem_used_bytes": max(mem_used_values) if mem_used_values else None,
        "start_peer_count": peer_values[0] if peer_values else None,
        "end_peer_count": peer_values[-1] if peer_values else None,
        "min_peer_count": min(peer_values) if peer_values else None,
        "max_peer_count": max(peer_values) if peer_values else None,
    }

    with open(args.output_json, "w") as handle:
        json.dump(summary, handle, indent=2)
        handle.write("\n")

    if samples:
        print(
            f"[node-monitor] collected {len(samples)} samples from {args.ssh_host}",
            file=sys.stderr,
        )
    else:
        print(
            f"[node-monitor] no samples collected from {args.ssh_host}; see error log if configured",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
