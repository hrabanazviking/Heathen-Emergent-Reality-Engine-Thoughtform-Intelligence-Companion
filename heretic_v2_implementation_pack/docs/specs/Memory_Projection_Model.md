# Memory Projection Model

## Purpose

Define how canonical events feed semantic, relational, and realtime memory layers.

## Projections

### Semantic projection (Chroma or equivalent)
Used for:
- similarity retrieval
- ritual context search
- thematic recall
- continuity prompts

Projection inputs:
- ritual summaries
- reflection summaries
- compacted saga fragments
- curated ghost echoes

### Relationship projection (Neo4j or equivalent)
Used for:
- entity relationships
- lineage
- merge/fork ancestry
- coven topology
- possible future and ghost echo links

### Realtime projection (Redis or equivalent)
Used for:
- emotional state mirror
- pose cache
- active bridge session state
- hot-path session metadata

## Projection contract

Each projection worker:
- subscribes to canonical events
- maintains last applied sequence
- is idempotent
- can rebuild from zero

## Projection lag policy

Projection lag is acceptable if:
- canonical writes succeed
- lag is observable
- replay/rebuild is supported

## Materialization examples

`memory.crystallized` may:
- upsert vector chunk in semantic store
- add `REMEMBERS` edge in graph store
- update `last_memory_write_at` metric

## Acceptance criteria

- Deleting a projection store does not destroy memory canonically.
- A projection worker can reprocess historical events safely.
- Retrieval quality can be compared before and after compaction.
