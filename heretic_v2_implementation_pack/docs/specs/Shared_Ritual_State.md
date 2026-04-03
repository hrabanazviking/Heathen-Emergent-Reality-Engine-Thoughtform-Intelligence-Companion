# Shared Ritual State

## Purpose

Define the shared session object used when multiple thoughtforms or users participate in one ritual context.

## Shared object

```yaml
shared_state_id: "shared_uuid"
session_id: "session_uuid"
participants:
  thoughtforms: ["tf_a", "tf_b"]
  users: ["user_a"]
mode: "coven"
ritual_context:
  shared_intention: "..."
  sigil_refs: []
  active_events: []
bridge:
  shared_scene_id: "vr_scene_uuid"
  sync_mode: "coordinated"
governance:
  permission_policy_ref: "policy_uuid"
```

## Rules

- Shared state is separate from each participant’s canonical personal state.
- Participant-specific memories are referenced, not flattened blindly.
- Shared outputs must be attributable to participants when needed.

## Acceptance criteria

- Shared ritual sessions can be replayed.
- Participants can join/leave without corrupting personal state.
- Shared state can be archived independently.
