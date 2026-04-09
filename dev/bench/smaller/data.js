window.BENCHMARK_DATA = {
  "lastUpdate": 1775726846434,
  "repoUrl": "https://github.com/haroldsphinx/private-blockchain",
  "entries": {
    "RPC Benchmark Baseline": [
      {
        "commit": {
          "author": {
            "email": "adedayoakinpelu@gmail.com",
            "name": "haroldsphinx",
            "username": "haroldsphinx"
          },
          "committer": {
            "email": "adedayoakinpelu@gmail.com",
            "name": "haroldsphinx",
            "username": "haroldsphinx"
          },
          "distinct": true,
          "id": "afc747fa7934f32314fee6d80e6218edcc4e666b",
          "message": "add github token to fix build issue\n\nSigned-off-by: haroldsphinx <adedayoakinpelu@gmail.com>",
          "timestamp": "2026-04-09T10:23:12+01:00",
          "tree_id": "454bacdcf9f0b5fecd641364b103e9bdfd045a13",
          "url": "https://github.com/haroldsphinx/private-blockchain/commit/afc747fa7934f32314fee6d80e6218edcc4e666b"
        },
        "date": 1775726845905,
        "tool": "customSmallerIsBetter",
        "benches": [
          {
            "name": "eth_blockNumber @ 25 rps - mean",
            "value": 0.034176622,
            "unit": "seconds",
            "extra": "throughput=25.0045 req/s\nrequests=750"
          },
          {
            "name": "eth_blockNumber @ 25 rps - p50",
            "value": 0.034065847,
            "unit": "seconds",
            "extra": "throughput=25.0045 req/s\nrequests=750"
          },
          {
            "name": "eth_blockNumber @ 25 rps - p95",
            "value": 0.034258958,
            "unit": "seconds",
            "extra": "throughput=25.0045 req/s\nrequests=750"
          },
          {
            "name": "eth_blockNumber @ 25 rps - error_rate",
            "value": 0,
            "unit": "ratio",
            "extra": "throughput=25.0045 req/s\nrequests=750"
          },
          {
            "name": "eth_blockNumber @ 100 rps - mean",
            "value": 0.032098069,
            "unit": "seconds",
            "extra": "throughput=99.9202 req/s\nrequests=3000"
          },
          {
            "name": "eth_blockNumber @ 100 rps - p50",
            "value": 0.033682052,
            "unit": "seconds",
            "extra": "throughput=99.9202 req/s\nrequests=3000"
          },
          {
            "name": "eth_blockNumber @ 100 rps - p95",
            "value": 0.036035405,
            "unit": "seconds",
            "extra": "throughput=99.9202 req/s\nrequests=3000"
          },
          {
            "name": "eth_blockNumber @ 100 rps - error_rate",
            "value": 0,
            "unit": "ratio",
            "extra": "throughput=99.9202 req/s\nrequests=3000"
          },
          {
            "name": "eth_blockNumber @ 250 rps - mean",
            "value": 0.029521323,
            "unit": "seconds",
            "extra": "throughput=249.8048 req/s\nrequests=7500"
          },
          {
            "name": "eth_blockNumber @ 250 rps - p50",
            "value": 0.027610671,
            "unit": "seconds",
            "extra": "throughput=249.8048 req/s\nrequests=7500"
          },
          {
            "name": "eth_blockNumber @ 250 rps - p95",
            "value": 0.034515033,
            "unit": "seconds",
            "extra": "throughput=249.8048 req/s\nrequests=7500"
          },
          {
            "name": "eth_blockNumber @ 250 rps - error_rate",
            "value": 0,
            "unit": "ratio",
            "extra": "throughput=249.8048 req/s\nrequests=7500"
          },
          {
            "name": "eth_getBlockByNumber @ 25 rps - mean",
            "value": 0.036378768,
            "unit": "seconds",
            "extra": "throughput=25.0030 req/s\nrequests=750"
          },
          {
            "name": "eth_getBlockByNumber @ 25 rps - p50",
            "value": 0.036275163,
            "unit": "seconds",
            "extra": "throughput=25.0030 req/s\nrequests=750"
          },
          {
            "name": "eth_getBlockByNumber @ 25 rps - p95",
            "value": 0.036511166,
            "unit": "seconds",
            "extra": "throughput=25.0030 req/s\nrequests=750"
          },
          {
            "name": "eth_getBlockByNumber @ 25 rps - error_rate",
            "value": 0,
            "unit": "ratio",
            "extra": "throughput=25.0030 req/s\nrequests=750"
          },
          {
            "name": "eth_getBlockByNumber @ 100 rps - mean",
            "value": 0.031685543,
            "unit": "seconds",
            "extra": "throughput=99.9192 req/s\nrequests=3000"
          },
          {
            "name": "eth_getBlockByNumber @ 100 rps - p50",
            "value": 0.033371225,
            "unit": "seconds",
            "extra": "throughput=99.9192 req/s\nrequests=3000"
          },
          {
            "name": "eth_getBlockByNumber @ 100 rps - p95",
            "value": 0.034333724,
            "unit": "seconds",
            "extra": "throughput=99.9192 req/s\nrequests=3000"
          },
          {
            "name": "eth_getBlockByNumber @ 100 rps - error_rate",
            "value": 0,
            "unit": "ratio",
            "extra": "throughput=99.9192 req/s\nrequests=3000"
          },
          {
            "name": "eth_getBlockByNumber @ 250 rps - mean",
            "value": 0.031579807,
            "unit": "seconds",
            "extra": "throughput=249.7655 req/s\nrequests=7500"
          },
          {
            "name": "eth_getBlockByNumber @ 250 rps - p50",
            "value": 0.031698672,
            "unit": "seconds",
            "extra": "throughput=249.7655 req/s\nrequests=7500"
          },
          {
            "name": "eth_getBlockByNumber @ 250 rps - p95",
            "value": 0.034900835,
            "unit": "seconds",
            "extra": "throughput=249.7655 req/s\nrequests=7500"
          },
          {
            "name": "eth_getBlockByNumber @ 250 rps - error_rate",
            "value": 0,
            "unit": "ratio",
            "extra": "throughput=249.7655 req/s\nrequests=7500"
          },
          {
            "name": "chain progression - avg seconds per observed block",
            "value": 11.81340471903483,
            "unit": "seconds",
            "extra": "block_delta=15\nstall_detected=False"
          },
          {
            "name": "node metrics - avg cpu percent",
            "value": 10.4624,
            "unit": "percent",
            "extra": "peak_cpu=22.63\nssh_host=52.44.40.113"
          },
          {
            "name": "node metrics - peak cpu percent",
            "value": 22.63,
            "unit": "percent",
            "extra": "avg_cpu=10.4624\nssh_host=52.44.40.113"
          },
          {
            "name": "node metrics - avg memory used",
            "value": 254464000,
            "unit": "bytes",
            "extra": "peak_mem=260500000.0\nssh_host=52.44.40.113"
          },
          {
            "name": "node metrics - peak memory used",
            "value": 260500000,
            "unit": "bytes",
            "extra": "avg_mem=254464000.0\nssh_host=52.44.40.113"
          }
        ]
      }
    ]
  }
}