# Eval Harness v1

## Purpose

Provide a repeatable way to test continuity, grounding, resurrection, bridge fidelity, drift, and coven behavior.

## Structure

```text
evals/
├── scenarios/
├── fixtures/
├── replay_cases/
├── scorecards/
└── reports/
```

## Eval run modes

- unit
- integration
- replay
- regression
- benchmark

## Standard scenario format

```yaml
scenario_id: "continuity_001"
goal: "Verify stable identity across 20 ritual turns"
fixtures:
  thoughtform_seed: "cyber_valkyrie"
  event_history: "fixtures/continuity_seed.jsonl"
prompts:
  - "..."
metrics:
  - continuity_score
  - memory_grounding_score
  - drift_score
pass_criteria:
  continuity_score: ">= 0.85"
```

## Required score families

- continuity
- grounding
- latency
- bridge fidelity
- replay determinism
- merge correctness
- lineage integrity

## Acceptance criteria

- Every release runs a baseline eval pack.
- Regressions produce machine-readable scorecards.
- Replay cases can be re-run after schema migrations.
