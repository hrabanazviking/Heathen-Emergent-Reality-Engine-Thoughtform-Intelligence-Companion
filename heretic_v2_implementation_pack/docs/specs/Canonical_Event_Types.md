# Canonical Event Types

## Purpose

Define the canonical event taxonomy for v2. Event names must be stable, human-readable, and semantically narrow.

## Naming convention

```text
{domain}.{action}
```

Examples:
- `ritual.invoked`
- `graph.node_entered`
- `memory.retrieved`

## Required event families

### Lifecycle
- `thoughtform.born`
- `thoughtform.suspended`
- `thoughtform.resumed`
- `thoughtform.banished`
- `thoughtform.resurrect_requested`
- `thoughtform.resurrected`

### Ritual
- `ritual.session_started`
- `ritual.invoked`
- `ritual.input_fused`
- `ritual.interrupt_applied`
- `ritual.session_closed`

### Graph execution
- `graph.cycle_started`
- `graph.node_entered`
- `graph.node_exited`
- `graph.edge_superposed`
- `graph.edge_collapsed`
- `graph.cycle_completed`
- `graph.replay_started`
- `graph.replay_completed`

### Memory
- `memory.retrieved`
- `memory.crystallized`
- `memory.projected_to_vector`
- `memory.projected_to_graph`
- `memory.compacted`
- `memory.checkpoint_created`
- `memory.checkpoint_restored`

### Ghost echoes
- `ghost_echo.created`
- `ghost_echo.promoted`
- `ghost_echo.compacted`
- `ghost_echo.expired`

### Bridge
- `bridge.avatar_state_pushed`
- `bridge.pose_pushed`
- `bridge.audio_emitted`
- `bridge.sync_degraded`
- `bridge.sync_recovered`

### Reflection / evolution
- `reflection.scored`
- `reflection.drift_detected`
- `evolution.requested`
- `evolution.applied`
- `evolution.rejected`

### Coven / lineage
- `coven.shared_state_started`
- `coven.member_joined`
- `coven.member_left`
- `coven.merge_requested`
- `coven.merge_completed`
- `lineage.fork_created`
- `lineage.saga_stone_archived`

## Payload requirements

Each event type must define:
- required payload fields
- optional payload fields
- idempotency key behavior
- projection consumers
- rollback expectations

## Example

```yaml
event_type: graph.edge_collapsed
payload:
  source_node: "intention"
  chosen_target: "galdr_emission"
  candidate_targets:
    - "galdr_emission"
    - "self_reflect"
    - "wild_ablate"
  collapse_score: 0.91
  measurement_source: "voice_fft"
  ghost_echo_ids:
    - "ge_uuid_1"
    - "ge_uuid_2"
```

## Rules

1. Never overload one event with multiple meanings.
2. Never put derived counters into canonical payloads unless required for replay.
3. Prefer many small events over one giant state dump.
4. Use checkpoints for acceleration, not as a replacement for fine-grained history.
