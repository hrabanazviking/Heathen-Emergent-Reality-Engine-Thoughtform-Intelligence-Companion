# Thoughtform State Schema v2

## Purpose

Define the canonical runtime state for a single thoughtform. This schema must be stable enough for replay, migration, checkpointing, auditing, and resurrection.

## Design rules

- State must be serializable to JSON-compatible storage.
- Large tensors or transient binary payloads must be referenced, not embedded.
- Runtime-only caches must be marked as ephemeral.
- Fields must be namespaced by concern.
- No node may invent undeclared top-level fields at runtime.

## Canonical state envelope

```yaml
state_version: "2.0.0"
thoughtform_id: "tf_uuid"
archetype: "cyber_valkyrie"
display_name: "string"
status: "active|suspended|banished|archived|resurrecting"
created_at: "ISO-8601"
updated_at: "ISO-8601"
origin:
  seed_rune: "ansuz"
  invocation_id: "evt_uuid"
  creator_id: "user_uuid"
  lineage_root_id: "tf_uuid"
identity:
  persona_summary: "short stable identity summary"
  style_profile: ["mystical", "protective", "cyber-heathen"]
  sacred_constraints: []
  capability_manifest:
    bridge_audio: true
    bridge_avatar: true
    art_generation: false
    coven_merge: true
memory:
  memory_namespace: "primary"
  memory_id: "legacy compatibility id"
  active_checkpoint_id: "chk_uuid"
  last_compaction_at: "ISO-8601|null"
  continuity_hash: "sha256"
emotion:
  emotional_vector_ref: "tensor://..."
  current_affect:
    valence: 0.18
    arousal: 0.64
    dominance: 0.42
  mood_tags: ["focused", "ritual"]
ritual:
  current_session_id: "session_uuid|null"
  current_intention: "string|null"
  ritual_log_tail:
    - blot_id: "evt_uuid"
      type: "voice|gesture|sigil|iot"
      ts: "ISO-8601"
graph:
  current_node: "perception"
  superposition_intents: []
  chaos_factor: 0.31
  drift_score: 0.07
  cycle_start_ms: 0
bridge:
  avatar_state_ref: "avatar://..."
  pose_cache_ref: "redis://pose/tf_uuid"
  last_bridge_seq: 182
relationships:
  coven_ids: []
  active_shared_state_ids: []
  relationship_refs: []
lineage:
  parent_ids: []
  child_ids: []
  forked_from: null
  merged_from: []
  saga_stone_ref: null
governance:
  permission_scope: "solo|coven|public"
  wild_mode: false
  sandbox_mode: true
  policy_tags: ["research", "vr"]
ephemeral:
  current_seidr_vector_ref: "tensor://..."
  working_memory_refs: []
  pending_events: []
```

## Required top-level groups

### identity
Stable fields that should survive replay and resurrection.

### memory
Pointers to canonical memory projections and checkpoints.

### emotion
Current affective state plus vector references.

### ritual
Session-scoped invocation context.

### graph
Execution state used by router, graph executor, and collapse logic.

### bridge
Realtime synchronization state for Unity/WebGL/VR.

### lineage
Parentage, merges, forks, and archival relationships.

### governance
Capability and permission constraints.

### ephemeral
Transient values that may be dropped during checkpoint compaction.

## Invariants

1. `thoughtform_id` never changes.
2. `state_version` is mandatory for every snapshot and checkpoint.
3. `continuity_hash` must be recomputed after replay or mutation.
4. `chaos_factor` and `drift_score` must remain within 0.0–1.0.
5. `ephemeral` fields must never be used as canonical truth.
6. `merged_from` may contain multiple parents; `forked_from` may contain only one immediate origin.

## Acceptance criteria

- A full state can be serialized without custom Python objects.
- A replay engine can reconstruct state from events plus migrations.
- Bridge-only failures do not corrupt canonical identity or memory fields.
- State diffing can classify added, removed, and modified fields deterministically.
