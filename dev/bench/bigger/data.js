window.BENCHMARK_DATA = {
  "lastUpdate": 1775726847664,
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
        "date": 1775726847255,
        "tool": "customBiggerIsBetter",
        "benches": [
          {
            "name": "eth_blockNumber @ 25 rps - throughput",
            "value": 25.004542284310617,
            "unit": "req/s",
            "extra": "mean=0.0342s\np95=0.0343s\nerrors=0"
          },
          {
            "name": "eth_blockNumber @ 100 rps - throughput",
            "value": 99.9202226583899,
            "unit": "req/s",
            "extra": "mean=0.0321s\np95=0.0360s\nerrors=0"
          },
          {
            "name": "eth_blockNumber @ 250 rps - throughput",
            "value": 249.8048195007698,
            "unit": "req/s",
            "extra": "mean=0.0295s\np95=0.0345s\nerrors=0"
          },
          {
            "name": "eth_getBlockByNumber @ 25 rps - throughput",
            "value": 25.003035310979772,
            "unit": "req/s",
            "extra": "mean=0.0364s\np95=0.0365s\nerrors=0"
          },
          {
            "name": "eth_getBlockByNumber @ 100 rps - throughput",
            "value": 99.91921465548423,
            "unit": "req/s",
            "extra": "mean=0.0317s\np95=0.0343s\nerrors=0"
          },
          {
            "name": "eth_getBlockByNumber @ 250 rps - throughput",
            "value": 249.76551912325948,
            "unit": "req/s",
            "extra": "mean=0.0316s\np95=0.0349s\nerrors=0"
          },
          {
            "name": "chain progression - block delta",
            "value": 15,
            "unit": "blocks",
            "extra": "start=4449\nend=4464\nstall_detected=False"
          },
          {
            "name": "node metrics - minimum peer count",
            "value": 2,
            "unit": "peers",
            "extra": "start=2\nend=2"
          }
        ]
      }
    ]
  }
}