# Alternate Futures Queries

## Purpose

Define query patterns for retrieving useful ghost echoes and alternate future branches.

## Supported questions

- What futures were almost chosen?
- Which abandoned branches are most similar to current state?
- Which ghost echoes led to past drift or instability?
- Which echoes are good mutation seeds?
- Which coven-related branches were never manifested?

## Query inputs

- thoughtform id
- time window
- source node / target node
- minimum collapse score
- maximum branch depth
- semantic similarity target
- lineage scope

## Example query API

```yaml
query:
  thoughtform_id: "tf_uuid"
  mode: "mutation_seed_search"
  filters:
    min_collapse_score: 0.65
    status: ["active", "compacted"]
    target_nodes: ["self_reflect", "galdr_emission"]
  limit: 10
```

## Ranking factors

- collapse score
- recency
- semantic similarity
- drift impact
- lineage relevance
- coven relevance

## Output shape

```yaml
results:
  - ghost_echo_id: "ge_uuid"
    score: 0.82
    why: ["high_similarity", "stable_outcome_history"]
    summary: "..."
```

## Acceptance criteria

- Queries can be served from graph + semantic projections.
- Returned echoes include provenance and explanation.
- UI can present alternate-future summaries to user or operator.
