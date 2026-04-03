# Coven Permissions Model

## Purpose

Define who may read, write, merge, or influence shared thoughtform state.

## Roles

- owner
- invited_member
- observer
- operator
- system

## Permission domains

- read_shared_state
- emit_shared_ritual_event
- request_merge
- approve_merge
- fork_from_shared_state
- view_lineage
- control_bridge

## Core rules

1. Solo-scoped thoughtforms cannot enter coven merge without explicit permission.
2. Merge requires all required approvers.
3. Observers cannot mutate shared ritual state.
4. Operators may intervene operationally but do not become lineage parents.

## Example policy

```yaml
policy:
  scope: "coven"
  approvals:
    merge: ["owner", "all_primary_participants"]
  deny:
    - observer: ["emit_shared_ritual_event", "request_merge"]
```

## Acceptance criteria

- Permission checks happen before state mutation.
- All coven actions are evented and auditable.
- Shared sessions can be inspected by participant and role.
