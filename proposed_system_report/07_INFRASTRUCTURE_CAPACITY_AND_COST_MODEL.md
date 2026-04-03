# Volume 7 — Infrastructure, Capacity, and Cost Model

## 1. Deployment Topology
- Multi-region active-active API + regional memory shards.
- Async event bus for memory promotion and analytic pipelines.
- Online feature store + offline warehouse mirror.

## 2. Capacity Model Assumptions
- DAU scenarios: 10k / 100k / 1M
- Average turns/session: 35
- Average tokens/turn: input 850, output 320
- Peak concurrency factor: 0.14

## 3. Cost Drivers
- LLM inference
- Embedding generation
- Vector storage and query
- Durable event storage
- Observability and logging retention

## 4. Example Sizing Code
```python
def monthly_token_cost(dau: int, turns: int, in_tok: int, out_tok: int, in_rate: float, out_rate: float) -> float:
    total_in = dau * 30 * turns * in_tok / 1_000_000
    total_out = dau * 30 * turns * out_tok / 1_000_000
    return total_in * in_rate + total_out * out_rate
```

## 5. FinOps Guardrails
- Per-tenant budget caps and adaptive model downgrades.
- Caching tiers with semantic dedupe.
- Real-time anomaly alerts for token burn spikes.
### 5.1 FinOps Control 1
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.2 FinOps Control 2
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.3 FinOps Control 3
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.4 FinOps Control 4
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.5 FinOps Control 5
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.6 FinOps Control 6
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.7 FinOps Control 7
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.8 FinOps Control 8
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.9 FinOps Control 9
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.10 FinOps Control 10
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.11 FinOps Control 11
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.12 FinOps Control 12
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.13 FinOps Control 13
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.14 FinOps Control 14
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.15 FinOps Control 15
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.16 FinOps Control 16
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.17 FinOps Control 17
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.18 FinOps Control 18
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.19 FinOps Control 19
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.20 FinOps Control 20
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.21 FinOps Control 21
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.22 FinOps Control 22
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.23 FinOps Control 23
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.24 FinOps Control 24
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.25 FinOps Control 25
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.26 FinOps Control 26
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.27 FinOps Control 27
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.28 FinOps Control 28
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.29 FinOps Control 29
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.30 FinOps Control 30
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.31 FinOps Control 31
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.32 FinOps Control 32
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.33 FinOps Control 33
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.34 FinOps Control 34
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.35 FinOps Control 35
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.36 FinOps Control 36
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.37 FinOps Control 37
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.38 FinOps Control 38
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.39 FinOps Control 39
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.

### 5.40 FinOps Control 40
- Control objective: prevent runaway cost while preserving quality SLO.
- Metric source: gateway telemetry + model router traces + storage accounting.
- Action: throttling, model reroute, cache boost, or deferred batch processing.
