#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import random
import sys
import time
import urllib.request

import flood


def rpc_call(url: str, method: str, params: list[object] | None = None) -> dict:
    if params is None:
        params = []
    payload = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    ).encode()
    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rpc-url", required=True)
    parser.add_argument("--method", required=True, choices=["eth_blockNumber", "eth_getBlockByNumber"])
    parser.add_argument("--label", required=True)
    parser.add_argument("--rates", required=True, nargs="+", type=int)
    parser.add_argument("--duration", required=True, type=int)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--workload-path", required=True)
    parser.add_argument("--workload-from")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--full-transactions", action="store_true")
    parser.add_argument("--verbose", type=int, default=1)
    return parser.parse_args()


def load_or_create_workload(args: argparse.Namespace) -> dict:
    workload_path = pathlib.Path(args.workload_path)
    if args.workload_from:
        workload = json.loads(pathlib.Path(args.workload_from).read_text())
        workload_path.parent.mkdir(parents=True, exist_ok=True)
        workload_path.write_text(json.dumps(workload, indent=2) + "\n")
        return workload
    if workload_path.exists():
        return json.loads(workload_path.read_text())

    block_number_response = rpc_call(args.rpc_url, "eth_blockNumber")
    latest_block = int(block_number_response["result"], 16)
    n_calls = sum(rate * args.duration for rate in args.rates)

    workload = {
        "seed": args.seed,
        "latest_block_at_generation": latest_block,
        "generated_at_epoch": int(time.time()),
        "tests": {
            "eth_blockNumber": {
                "calls": [
                    {"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber", "params": []}
                    for _ in range(n_calls)
                ]
            }
        },
    }

    rng = random.Random(args.seed)
    block_numbers = [rng.randint(0, latest_block) for _ in range(n_calls)]
    workload["tests"]["eth_getBlockByNumber"] = {
        "block_numbers": [hex(block_number) for block_number in block_numbers],
        "full_transactions": args.full_transactions,
    }
    workload_path.parent.mkdir(parents=True, exist_ok=True)
    workload_path.write_text(json.dumps(workload, indent=2) + "\n")
    return workload


def build_calls(method: str, workload: dict) -> list[dict]:
    if method == "eth_blockNumber":
        return workload["tests"]["eth_blockNumber"]["calls"]
    if method == "eth_getBlockByNumber":
        full_transactions = workload["tests"]["eth_getBlockByNumber"]["full_transactions"]
        return [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "eth_getBlockByNumber",
                "params": [block_number, full_transactions],
            }
            for block_number in workload["tests"]["eth_getBlockByNumber"]["block_numbers"]
        ]
    raise ValueError(f"unsupported method: {method}")


def create_test(method: str, calls: list[dict], rates: list[int], duration: int) -> dict:
    attacks = []
    cursor = 0
    for rate in rates:
        n_calls = rate * duration
        if len(calls[cursor : cursor + n_calls]) < n_calls:
            raise ValueError(f"insufficient calls prepared for {method} at rate {rate}")
        attacks.append(
            {
                "rate": rate,
                "duration": duration,
                "vegeta_args": None,
                "calls": calls[cursor : cursor + n_calls],
            }
        )
        cursor += n_calls
    return {"attacks": attacks}


def summarize_result(result: dict) -> dict:
    rows = []
    for index, rate in enumerate(result["target_rate"]):
        success = result["success"][index]
        error_rate = None if success is None else 1 - success
        rows.append(
            {
                "rate": rate,
                "target_duration": result["target_duration"][index],
                "requests": result["requests"][index],
                "throughput": result["throughput"][index],
                "mean": result["mean"][index],
                "p50": result["p50"][index],
                "p95": result["p95"][index],
                "p99": result["p99"][index],
                "success": success,
                "error_rate": error_rate,
                "errors": result["errors"][index],
                "status_codes": result["status_codes"][index],
            }
        )
    return {"rows": rows}


def save_results_payload(
    *,
    output_dir: pathlib.Path,
    label: str,
    node: dict,
    results: dict,
    t_run_start: float,
    t_run_end: float,
) -> dict:
    payload = {
        "flood_version": getattr(flood, "__version__", None),
        "dependency_versions": {},
        "cli_args": list(sys.argv),
        "type": "single_test",
        "t_run_start": t_run_start,
        "t_run_end": t_run_end,
        "nodes": {label: node},
        "results": results,
    }
    (output_dir / "results.json").write_text(json.dumps(payload, indent=2) + "\n")
    return payload


def main() -> None:
    args = parse_args()
    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    workload = load_or_create_workload(args)
    calls = build_calls(args.method, workload)
    test = create_test(args.method, calls, args.rates, args.duration)

    node = {
        "name": args.label,
        "url": args.rpc_url,
        "remote": None,
        "client_version": None,
        "network": None,
    }

    t_run_start = time.time()
    results = flood.run_load_tests(
        node=node,
        test=test,
        verbose=bool(args.verbose),
    )
    t_run_end = time.time()

    payload = save_results_payload(
        output_dir=output_dir,
        label=args.label,
        node=node,
        results=results,
        t_run_start=t_run_start,
        t_run_end=t_run_end,
    )

    custom_test = {
        "name": args.method,
        "method": args.method,
        "rates": args.rates,
        "duration": args.duration,
        "workload_source": args.workload_from,
        "rpc_url": args.rpc_url,
    }
    (output_dir / "test.json").write_text(json.dumps(custom_test, indent=2) + "\n")

    summary = summarize_result(payload["results"][args.label])
    (output_dir / "metrics.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
