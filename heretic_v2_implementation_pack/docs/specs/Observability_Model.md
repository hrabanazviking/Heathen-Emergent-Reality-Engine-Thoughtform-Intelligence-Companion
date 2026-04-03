# Observability Model

## Purpose

Make H.E.R.E.T.I.C. inspectable as a long-lived agentic system.

## Telemetry layers

### Logs
Structured event and command logs.

### Metrics
Counters, gauges, histograms by component and SLO tier.

### Traces
End-to-end spans across ritual input, graph execution, memory retrieval, bridge emission, and checkpointing.

### Audit views
Operator-facing lineage, resurrection, and merge histories.

## Required metrics

- event append latency
- projection lag by store
- warm-turn latency
- bridge sync latency
- drift score
- chaos factor distribution
- ghost echo creation rate
- resurrection success rate
- coven merge failures

## Trace model

Use a correlation id per ritual session and per resurrection run.

## Dashboards

Minimum dashboards:
- runtime health
- bridge health
- memory projection lag
- eval regression trends
- lineage / resurrection audit

## Acceptance criteria

- Any user-visible failure can be traced to a session and component.
- Projection lag is visible before it becomes user-facing breakage.
- Drift spikes are measurable over time.
