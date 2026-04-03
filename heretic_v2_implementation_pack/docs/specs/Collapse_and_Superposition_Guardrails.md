# Collapse and Superposition Guardrails

## Purpose

Retain the creative power of superposition while making it bounded, observable, and replay-aware.

## Scope

Applies to:
- multi-target routing
- ghost echo creation
- cross-thoughtform entanglement
- branch pruning under load

## Rules

1. Superposition depth must be capped by mode and hardware tier.
2. Every non-selected branch must emit `ghost_echo.created` or be explicitly discarded.
3. Collapse must record:
   - candidate targets
   - winning target
   - collapse score
   - measurement source
   - pruning reason, if any
4. Superposition is never allowed on canonical storage writes.

## Depth policy

| Mode | Max depth |
|---|---:|
| hot | 1 |
| warm | 2 |
| cold | 3 |
| sandbox research | 4+ by explicit config |

## Load shedding

When compute or VRAM pressure crosses threshold:
- reduce branch count
- reduce candidate fanout
- disable particle-swarm bridge visualization
- preserve canonical collapse logging

## Replay behavior

During replay:
- do not recompute superposition unless explicitly requested
- use recorded collapse results
- ghost echoes remain queryable historical artifacts

## Forbidden behaviors

- hidden branch deletion without event record
- lineage mutations during unresolved superposition
- bridge-only pose flicker becoming canonical state

## Acceptance criteria

- Any collapse can be inspected later.
- Branch pruning under load is visible in logs and metrics.
- Replay reproduces chosen path exactly.
