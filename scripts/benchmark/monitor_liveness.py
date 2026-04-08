#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import signal
import time
import urllib.request


RUNNING = True


def handle_signal(signum, frame):  # type: ignore[no-untyped-def]
    global RUNNING
    RUNNING = False


def rpc_call(url: str, method: str) -> dict:
    payload = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": []}
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
    parser.add_argument("--poll-interval", type=int, default=5)
    parser.add_argument("--stall-threshold", type=int, default=60)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-csv", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    samples: list[dict[str, int | float]] = []

    while RUNNING:
        timestamp = time.time()
        response = rpc_call(args.rpc_url, "eth_blockNumber")
        height = int(response["result"], 16)
        samples.append({"timestamp": timestamp, "height": height})
        time.sleep(args.poll_interval)

    with open(args.output_csv, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["timestamp", "height"])
        writer.writeheader()
        writer.writerows(samples)

    starting_block = samples[0]["height"] if samples else None
    ending_block = samples[-1]["height"] if samples else None
    block_delta = (
        None if starting_block is None or ending_block is None else ending_block - starting_block
    )

    last_height = None
    last_increase_time = None
    stall_detected = False
    longest_stall = 0.0
    for sample in samples:
        height = sample["height"]
        timestamp = sample["timestamp"]
        if last_height is None or height > last_height:
            if last_increase_time is not None:
                longest_stall = max(longest_stall, timestamp - last_increase_time)
            last_increase_time = timestamp
        last_height = height

    if len(samples) >= 2:
        trailing_stall = samples[-1]["timestamp"] - (last_increase_time or samples[0]["timestamp"])
        longest_stall = max(longest_stall, trailing_stall)
        stall_detected = longest_stall >= args.stall_threshold

    average_seconds_per_observed_block = None
    if block_delta and block_delta > 0:
        average_seconds_per_observed_block = (
            samples[-1]["timestamp"] - samples[0]["timestamp"]
        ) / block_delta

    summary = {
        "rpc_url": args.rpc_url,
        "poll_interval_seconds": args.poll_interval,
        "stall_threshold_seconds": args.stall_threshold,
        "samples": len(samples),
        "starting_block": starting_block,
        "ending_block": ending_block,
        "block_delta": block_delta,
        "average_seconds_per_observed_block": average_seconds_per_observed_block,
        "longest_stall_seconds": longest_stall,
        "stall_detected": stall_detected,
    }

    with open(args.output_json, "w") as handle:
        json.dump(summary, handle, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main()
