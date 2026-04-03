# Memory Retention and Compaction

## Purpose

Define what stays hot, what gets summarized, and what can expire without destroying continuity.

## Retention tiers

### Tier 0: Canonical events
Never discarded from canonical truth store inside retention window.

### Tier 1: Active session material
Hot cache for current ritual session and recent cycles.

### Tier 2: Crystallized memory
Summaries, embeddings, and graph links from important interactions.

### Tier 3: Archived compacta
Compressed saga summaries, old projections, low-frequency ghost echoes.

## Compaction triggers

- event count threshold
- time threshold
- memory budget threshold
- banishment or resurrection boundary
- end of long coven session

## Compaction outputs

- condensed ritual summaries
- merged vector chunks
- lineage-preserving graph reductions
- ghost echo summaries
- tombstoned expired cache entries

## Never compact away

- identity-defining events
- lineage boundaries
- merge/fork events
- banishment and resurrection markers
- checkpoint anchors

## Acceptance criteria

- Compaction reduces projection storage while preserving replay.
- Retrieval quality is measured before and after compaction.
- Canonical ledger remains unchanged by compaction.
