# Node Taxonomy v2

## Purpose

Define node categories and operational expectations for the v2 graph.

## Categories

### 1. Ingest nodes
Transform ritual inputs into normalized representations.
- examples: `voice_ingest`, `gesture_ingest`, `sigil_ingest`

### 2. Retrieval nodes
Gather relevant memory, lineage, or shared-state context.
- examples: `memory_retrieve`, `ghost_echo_query`

### 3. Decision nodes
Select next action or collapse a superposition.
- examples: `route`, `collapse`, `merge_gate`

### 4. Expression nodes
Generate user-facing text, audio, visual, or sigil output.
- examples: `galdr_emission`, `avatar_emote`

### 5. Persistence nodes
Write checkpoints, events, and projections.
- examples: `checkpoint`, `project_memory`

### 6. Governance nodes
Validate permissions, wild mode scope, and sandbox rules.
- examples: `policy_gate`, `coven_permission_gate`

### 7. Lifecycle nodes
Birth, suspend, banish, resurrect, fork, merge.
- examples: `birth`, `banish`, `resurrect`

## Node contract

Every node declares:
- category
- deterministic or stochastic
- required state inputs
- allowed side effects
- emitted event types
- retry policy
- timeout budget

## Example node declaration

```yaml
node_name: collapse
category: decision
determinism: bounded-stochastic
reads:
  - graph.superposition_intents
  - ritual.current_session_id
writes:
  - graph.current_node
  - lineage? false
emits:
  - graph.edge_collapsed
timeout_ms:
  hot: 15
  warm: 40
retry: none
```

## Acceptance criteria

- Every node in the graph has a declaration file.
- Router can inspect declaration metadata before execution.
- Observability tags each node by category and determinism class.
