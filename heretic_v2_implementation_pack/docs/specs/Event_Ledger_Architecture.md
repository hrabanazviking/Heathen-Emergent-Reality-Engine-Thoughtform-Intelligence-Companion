# Event Ledger Architecture

## Purpose

Define the append-only event ledger that becomes the canonical truth source for H.E.R.E.T.I.C. v2.

## Why this exists

The current system already behaves like a saga of ritual actions, graph transitions, memory writes, bridge emissions, reflection scores, and ghost-echo archives. v2 formalizes that history into a ledger.

## Core rule

**No projection is authoritative.**
- Chroma = semantic projection
- Neo4j = relationship projection
- Redis = realtime cache
- Checkpoints = replay acceleration
- Event ledger = truth

## Event stream model

Each thoughtform has a primary stream:

```text
stream_id = thoughtform:{thoughtform_id}
```

Additional streams may exist for:
- ritual sessions
- shared coven state
- bridge channels
- admin operations

## Event envelope

```json
{
  "event_id": "evt_uuid",
  "stream_id": "thoughtform:tf_uuid",
  "sequence": 1042,
  "event_type": "graph.node_entered",
  "schema_version": "1.0.0",
  "occurred_at": "2026-04-02T20:11:35Z",
  "causation_id": "evt_parent_uuid",
  "correlation_id": "session_uuid_or_trace_uuid",
  "actor": {
    "type": "user|thoughtform|system|bridge",
    "id": "user_uuid"
  },
  "payload": {},
  "meta": {
    "environment": "local-dev",
    "trace_id": "trace_uuid",
    "hot_warm_cold": "warm"
  }
}
```

## Required guarantees

1. Per-stream ordering is strict.
2. Sequence numbers are contiguous inside a stream.
3. Events are immutable after commit.
4. Projections are idempotent and replay-safe.
5. Events can be re-read by sequence range or correlation id.

## Storage strategy

### Canonical store
Use a durable append-only store. Early implementations can use PostgreSQL with:
- `events` table
- unique `(stream_id, sequence)`
- indexed `event_type`, `occurred_at`, `correlation_id`

### Checkpoints
Store compacted snapshots every N events or on major lifecycle transitions:
- thoughtform birth
- post-resurrection
- post-merge
- banishment
- post-compaction

### Projection workers
Independent workers consume events and update:
- Neo4j relationships
- Chroma memory chunks
- Redis realtime mirrors
- observability counters
- audit materializations

## Command flow

```text
command -> validate -> emit event(s) -> persist -> ack -> project asynchronously
```

Commands never mutate projections directly.

## Failure policy

- If projection fails, canonical write still stands.
- Failed projections are retried from last acknowledged sequence.
- Replay can rebuild any projection from the ledger plus checkpoints.

## Acceptance criteria

- A deleted projection store can be rebuilt from events.
- A thoughtform can be rehydrated using ledger + latest compatible checkpoint.
- Multiple projections can consume the same event stream without coordination bugs.
