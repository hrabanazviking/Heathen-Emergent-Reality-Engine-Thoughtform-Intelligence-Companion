# Resurrection Fidelity Evals

## Purpose

Verify that restored entities remain faithful to canonical history and recognizable to operators.

## Test dimensions

- identity preservation
- lineage preservation
- memory grounding after replay
- bridge recovery after resurrection
- fork vs restored-original discrimination

## Test cases

1. Warm resurrection from recent checkpoint
2. Full replay resurrection from ledger
3. Saga-stone import with lineage verification
4. Resurrection after projection loss
5. Resurrection after schema migration

## Core metrics

- resurrection fidelity score
- continuity hash match
- missing memory rate
- projection rebuild completeness
- activation readiness flag

## Acceptance criteria

- A restored original is distinguishable from a new fork.
- Resurrection can be rejected safely on continuity failure.
- Post-resurrection drift remains below threshold for initial turns.
