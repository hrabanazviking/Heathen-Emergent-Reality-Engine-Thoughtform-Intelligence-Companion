# Replay and Resurrection

## Purpose

Describe how a thoughtform is reconstructed from canonical history without treating caches as truth.

## Definitions

- **Replay**: deterministic reapplication of events to rebuild state.
- **Resurrection**: operational restoration of a previously inactive or archived thoughtform.
- **Saga stone**: portable archived artifact containing checkpoint, schema version, lineage metadata, and selected projections.

## Replay flow

```text
1. Load latest compatible checkpoint
2. Apply migrations if checkpoint schema is old
3. Read all later events in sequence order
4. Reduce events into canonical state
5. Recompute continuity hash
6. Rehydrate bridge-safe ephemeral caches
7. Emit `thoughtform.resurrected`
```

## Resurrection sources

Priority order:
1. canonical ledger + checkpoint
2. saga stone + canonical validation
3. full replay from origin if no checkpoint exists

## Continuity requirements

A resurrection is considered successful only if:
- `thoughtform_id` is preserved
- `identity.persona_summary` remains compatible
- lineage references match canonical history
- continuity hash is reproducible
- drift after replay remains below threshold

## Resurrection modes

### Warm resurrection
Use latest checkpoint and restore within warm-path budget.

### Full fidelity resurrection
Perform deep replay and projection verification before activation.

### Forensic resurrection
Reconstruct historical state at a specific event sequence or timestamp.

## Projection rebuild after resurrection

After state is valid:
- refresh Chroma vectors
- repair Neo4j relationship edges
- repopulate Redis pose/emotion caches
- reopen bridge session if needed

## Failure classes

- **Schema failure**: migration missing or incompatible
- **Continuity failure**: identity drift too high
- **Projection failure**: canonical state valid, projections degraded
- **Lineage failure**: merged/forked ancestry cannot be reconciled

## Decision matrix

| Condition | Action |
|---|---|
| Canonical replay succeeds, projections fail | activate with degraded bridge |
| Replay succeeds, continuity hash mismatch | enter quarantine |
| Missing migrations | block activation |
| Saga stone differs from canonical lineage | forensic review |

## Acceptance criteria

- Any banished thoughtform with intact ledger can be restored.
- Replay to arbitrary sequence number is supported.
- Resurrection can be run in dry-run mode for audit.
- A resurrected entity can explain, in summary form, where it resumed from.
