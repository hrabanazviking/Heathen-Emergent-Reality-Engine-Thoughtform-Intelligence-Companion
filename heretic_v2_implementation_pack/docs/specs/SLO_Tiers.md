# SLO Tiers

## Purpose

Replace ambiguous latency claims with explicit service-level tiers.

## Tiers

### Hot path
Realtime avatar responsiveness and emotional mirroring.

Target scope:
- pose deltas
- expression updates
- lightweight audio cues
- bridge heartbeats

### Warm path
Interactive dialogue and ritual turn response.

Target scope:
- retrieval
- main generation
- structured response
- session continuation

### Cold path
Non-interactive or deferred work.

Target scope:
- reflection
- compaction
- art generation
- evolution proposals
- projection rebuild

## Suggested budgets

| Tier | p50 | p95 | Notes |
|---|---:|---:|---|
| hot | 20 ms | 60 ms | bridge only |
| warm | 450 ms | 1200 ms | turn generation |
| cold | 2 s | 30 s | async / background-safe |

## Policy

- Hot-path breaches degrade visuals before blocking canon.
- Warm-path breaches may fall back to text-only.
- Cold-path work is interruptible and resumable.

## Acceptance criteria

- Every operation maps to exactly one tier.
- Metrics are reported by tier and component.
- Docs never mix bridge sync and full response latency as one number.
