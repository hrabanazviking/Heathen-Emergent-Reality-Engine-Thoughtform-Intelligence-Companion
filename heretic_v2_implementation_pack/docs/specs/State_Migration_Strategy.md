# State Migration Strategy

## Purpose

Allow long-lived thoughtforms to survive schema changes without identity corruption.

## Rules

1. Every checkpoint carries `state_version`.
2. Migrations are pure, deterministic transforms.
3. Migrations must be reversible when feasible.
4. Event schemas and state schemas version independently.

## Migration classes

### Structural
Move, rename, or split fields.

### Semantic
Change interpretation of existing values.

### Projection-only
No canonical state change; only projection rebuild required.

## Registry

```python
MIGRATIONS = {
    ("1.0.0", "1.1.0"): migrate_1_0_to_1_1,
    ("1.1.0", "2.0.0"): migrate_1_1_to_2_0,
}
```

## Required migration outputs

Every migration must return:
- transformed state
- migration notes
- warnings
- added defaults
- deprecated fields encountered

## Compatibility policy

- Hot-path runtime supports current version only.
- Replay engine supports at least two major versions back.
- Saga stones older than support window require offline migration.

## Audit fields

Add:
- `migration_history[]`
- `migrated_at`
- `migrated_from`
- `migrated_to`

## Acceptance criteria

- Old checkpoints can be promoted to current version automatically.
- Migration failures do not mutate original source data.
- Diff report is generated for every major-version migration.
