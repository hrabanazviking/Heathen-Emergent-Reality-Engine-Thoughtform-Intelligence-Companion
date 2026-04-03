# 04 — Agents and Skills Code Ideas

## A. Agent Topology

### Idea A1: Triad Agent Pattern
- `CompanionAgent`: user-facing conversational layer
- `StewardAgent`: safety + policy + consent mediator
- `BuilderAgent`: planning and tool execution
- Merge outputs through arbitration protocol.

### Idea A2: Subagent Contract Schema
- Required contract fields:
  - input schema
  - expected latency
  - failure types
  - fallback strategy
  - observability hooks

### Idea A3: Dynamic Agent Spawning
- Spawn specialist agents only when task complexity threshold is crossed.
- Use hard token and time budgets for spawned workers.

## B. Skills Framework

### Idea B1: Skill Manifest v2
- Add fields:
  - risk level
  - data access class
  - deterministic mode support
  - test fixtures path

### Idea B2: Skill Reliability Scoring
- Compute rolling score from:
  - success rate
  - median latency
  - user correction frequency
- Use score during tool routing.

### Idea B3: Skill Sandboxing Matrix
- Per-skill permissions:
  - file read/write roots
  - network allow-list
  - command prefix allow-list

## C. Multi-Agent Collaboration

### Idea C1: Debate-then-Decide Protocol
- Two planning agents generate competing plans.
- Judge agent selects plan with best safety and evidence profile.

### Idea C2: Shared Scratchpad with Redaction
- Shared workspace for subagents with policy-driven redaction.
- Prevents leakage of sensitive segments.

### Idea C3: Reflection Agent
- Post-task reflection writes:
  - what worked
  - what failed
  - mitigation candidates
- Feeds an automated improvement backlog.
