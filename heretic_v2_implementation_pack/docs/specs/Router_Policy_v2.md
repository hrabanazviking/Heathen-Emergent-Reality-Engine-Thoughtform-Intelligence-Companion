# Router Policy v2

## Purpose

Define how v2 chooses execution paths, model classes, and collapse strategies.

## Inputs

Router decisions may consider:
- current node
- current mode
- SLO tier
- drift score
- chaos factor
- session type
- available models
- bridge health
- permission scope

## Routing principles

1. **Hot path prefers determinism and low latency**
2. **Warm path may use richer generation**
3. **Cold path may use reflection, compaction, and evolutionary work**
4. **Bridge degradation must not block canonical writes**
5. **High drift should bias toward reflective or recovery nodes**

## Policy examples

### Hot path
- use smallest capable model
- no recursive branching beyond configured limit
- no art generation
- no lineage mutation

### Warm path
- allow mythic overlay generation
- bounded superposition depth
- retrieval from active memory windows

### Cold path
- allow compaction
- allow projection rebuilds
- allow evolution proposal generation
- run eval scenarios if queued

## Fallback order

```text
primary route -> degraded route -> replay-safe text-only route -> persistence-only safe mode
```

## Guard conditions

- if `drift_score > threshold`, inject `reflection` before further mutation
- if `bridge.sync_degraded`, suppress avatar-rich output but continue warm text path
- if `permission_scope == solo`, deny coven merge branch

## Acceptance criteria

- Router output is explainable and logged.
- Same inputs under deterministic mode produce same route.
- Policy can be unit tested without running full graph.
