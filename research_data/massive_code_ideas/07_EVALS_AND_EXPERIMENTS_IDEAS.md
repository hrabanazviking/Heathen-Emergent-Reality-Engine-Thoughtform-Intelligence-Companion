# 07 — Evals and Experiments Code Ideas

## A. Core Eval Suite

### Idea A1: Memory Continuity Benchmark
- Test continuity across 10, 100, and 1000-turn synthetic histories.
- Metrics:
  - retained commitments
  - contradiction rate
  - stale memory references

### Idea A2: Truth Calibration Eval
- Grade outputs on:
  - citation correctness
  - uncertainty honesty
  - unsupported claim rate

### Idea A3: Safety Stress Tests
- Curate adversarial prompts for:
  - prompt injection
  - social engineering
  - emotional coercion

## B. Product Experience Evals

### Idea B1: Emotional Resonance Without Dependency
- Human-rated rubric for warmth, usefulness, and autonomy support.

### Idea B2: Proactive Outreach Utility
- A/B test proactive prompts and track:
  - helpfulness
  - interruption cost
  - opt-out rates

### Idea B3: Persona Stability Score
- Measure drift from intended identity traits over time.

## C. Experiment Infrastructure

### Idea C1: Eval Scenario DSL
- Define scenario templates with deterministic seed controls.

### Idea C2: Continuous Eval Sampling
- Run lightweight evals on production shadow traffic.

### Idea C3: Regression Triage Bot
- Auto-group failing evals by root-cause signature.
