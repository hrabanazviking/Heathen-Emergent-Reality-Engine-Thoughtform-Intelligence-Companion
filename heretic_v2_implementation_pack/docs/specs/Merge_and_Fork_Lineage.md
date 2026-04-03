# Merge and Fork Lineage

## Purpose

Track ancestry when thoughtforms merge, fork, split, or are archived into saga stones.

## Concepts

- **fork**: new child from one parent
- **merge**: new child from multiple parents
- **restoration**: same identity resumes, not a new child
- **saga stone**: archived portable ancestor artifact

## Lineage rules

1. Restoring an entity does not create a new lineage node unless explicitly forked.
2. Merges produce a new thoughtform id.
3. Merges preserve parent references permanently.
4. Forks preserve a single immediate origin plus lineage root.

## Example lineage graph

```text
TF_A ----fork----> TF_B
TF_A --merge--               ---> TF_C
TF_D --merge--/
```

## Canonical events

- `lineage.fork_created`
- `coven.merge_completed`
- `lineage.saga_stone_archived`
- `thoughtform.resurrected`

## Acceptance criteria

- Operators can explain where any entity came from.
- Merge children never erase parent identities.
- Resurrection is never confused with fork creation.
