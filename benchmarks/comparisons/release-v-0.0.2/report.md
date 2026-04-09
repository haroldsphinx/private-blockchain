# Benchmark Comparison

- Current run: `.baseline/results/current/20260409T103442Z`
- Candidate run: `results/candidate/20260409T104349Z`
- Current EL client: `Geth/v1.16.7-stable-b9f3a3d9/linux-amd64/go1.24.9`
- Candidate EL client: `Geth/v1.16.8-stable-abeb78c6/linux-amd64/go1.24.11`
- Current CL client: `Lighthouse/v8.1.0-edba56b/x86_64-linux`
- Candidate CL client: `Lighthouse/v8.1.0-edba56b/x86_64-linux`

## RPC Metrics

| Test | Rate | Metric | Current | Candidate | Delta | % Delta | Verdict |
| --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| eth_blockNumber | 25 | mean | 0.0068 | 0.0028 | -0.0040 | -58.76% | improved |
| eth_blockNumber | 25 | p50 | 0.0067 | 0.0027 | -0.0040 | -60.40% | improved |
| eth_blockNumber | 25 | p95 | 0.0075 | 0.0036 | -0.0038 | -51.32% | improved |
| eth_blockNumber | 25 | throughput | 25.0279 | 25.0308 | 0.0029 | 0.01% | unchanged |
| eth_blockNumber | 25 | error_rate | 0.0000 | 0.0000 | 0.0000 | n/a | unchanged |
| eth_blockNumber | 100 | mean | 0.0068 | 0.0034 | -0.0034 | -50.64% | improved |
| eth_blockNumber | 100 | p50 | 0.0069 | 0.0032 | -0.0037 | -53.25% | improved |
| eth_blockNumber | 100 | p95 | 0.0074 | 0.0039 | -0.0035 | -47.54% | improved |
| eth_blockNumber | 100 | throughput | 100.0117 | 100.0214 | 0.0097 | 0.01% | unchanged |
| eth_blockNumber | 100 | error_rate | 0.0000 | 0.0000 | 0.0000 | n/a | unchanged |
| eth_blockNumber | 250 | mean | 0.0067 | 0.0025 | -0.0042 | -62.45% | improved |
| eth_blockNumber | 250 | p50 | 0.0066 | 0.0025 | -0.0042 | -62.86% | improved |
| eth_blockNumber | 250 | p95 | 0.0072 | 0.0030 | -0.0042 | -57.90% | improved |
| eth_blockNumber | 250 | throughput | 249.9777 | 250.0105 | 0.0328 | 0.01% | unchanged |
| eth_blockNumber | 250 | error_rate | 0.0000 | 0.0000 | 0.0000 | n/a | unchanged |
| eth_call | 25 | mean | 0.0067 | 0.0040 | -0.0027 | -39.92% | improved |
| eth_call | 25 | p50 | 0.0065 | 0.0039 | -0.0027 | -40.81% | improved |
| eth_call | 25 | p95 | 0.0074 | 0.0048 | -0.0026 | -34.87% | improved |
| eth_call | 25 | throughput | 25.0272 | 25.0302 | 0.0029 | 0.01% | unchanged |
| eth_call | 25 | error_rate | 0.0000 | 0.0000 | 0.0000 | n/a | unchanged |
| eth_call | 100 | mean | 0.0069 | 0.0027 | -0.0042 | -60.44% | improved |
| eth_call | 100 | p50 | 0.0068 | 0.0026 | -0.0043 | -62.27% | improved |
| eth_call | 100 | p95 | 0.0075 | 0.0034 | -0.0041 | -54.34% | improved |
| eth_call | 100 | throughput | 100.0108 | 100.0253 | 0.0146 | 0.01% | unchanged |
| eth_call | 100 | error_rate | 0.0000 | 0.0000 | 0.0000 | n/a | unchanged |
| eth_call | 250 | mean | 0.0070 | 0.0029 | -0.0041 | -58.44% | improved |
| eth_call | 250 | p50 | 0.0069 | 0.0027 | -0.0042 | -60.56% | improved |
| eth_call | 250 | p95 | 0.0078 | 0.0039 | -0.0039 | -49.44% | improved |
| eth_call | 250 | throughput | 249.9721 | 250.0103 | 0.0382 | 0.02% | unchanged |
| eth_call | 250 | error_rate | 0.0000 | 0.0000 | 0.0000 | n/a | unchanged |
| eth_getBlockByNumber | 25 | mean | 0.0069 | 0.0038 | -0.0030 | -43.96% | improved |
| eth_getBlockByNumber | 25 | p50 | 0.0068 | 0.0038 | -0.0031 | -44.86% | improved |
| eth_getBlockByNumber | 25 | p95 | 0.0072 | 0.0043 | -0.0029 | -40.15% | improved |
| eth_getBlockByNumber | 25 | throughput | 25.0275 | 25.0301 | 0.0026 | 0.01% | unchanged |
| eth_getBlockByNumber | 25 | error_rate | 0.0000 | 0.0000 | 0.0000 | n/a | unchanged |
| eth_getBlockByNumber | 100 | mean | 0.0070 | 0.0034 | -0.0037 | -52.12% | improved |
| eth_getBlockByNumber | 100 | p50 | 0.0069 | 0.0032 | -0.0037 | -53.96% | improved |
| eth_getBlockByNumber | 100 | p95 | 0.0075 | 0.0040 | -0.0035 | -46.54% | improved |
| eth_getBlockByNumber | 100 | throughput | 100.0100 | 100.0202 | 0.0102 | 0.01% | unchanged |
| eth_getBlockByNumber | 100 | error_rate | 0.0000 | 0.0000 | 0.0000 | n/a | unchanged |
| eth_getBlockByNumber | 250 | mean | 0.0066 | 0.0031 | -0.0035 | -53.44% | improved |
| eth_getBlockByNumber | 250 | p50 | 0.0065 | 0.0031 | -0.0034 | -52.46% | improved |
| eth_getBlockByNumber | 250 | p95 | 0.0073 | 0.0038 | -0.0035 | -47.73% | improved |
| eth_getBlockByNumber | 250 | throughput | 249.9783 | 249.9985 | 0.0202 | 0.01% | unchanged |
| eth_getBlockByNumber | 250 | error_rate | 0.0000 | 0.0000 | 0.0000 | n/a | unchanged |

## Liveness

| Run | Start Block | End Block | Block Delta | Avg Seconds Per Block Increase | Stall Detected |
| --- | ---: | ---: | ---: | ---: | --- |
| current | 0 | 0 | 0 | n/a | yes |
| candidate | 0 | 0 | 0 | n/a | yes |

## Node Metrics

| Run | Avg CPU % | Peak CPU % | Avg Memory | Peak Memory | Start Peers | End Peers | Min Peers |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| current | 13.1593 | 33.5300 | 64.67 MiB | 66.28 MiB | 0 | 0 | 0 |
| candidate | 14.0232 | 32.1700 | 43.06 MiB | 45.08 MiB | 2 | 2 | 2 |

