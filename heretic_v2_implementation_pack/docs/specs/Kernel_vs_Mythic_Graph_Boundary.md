# Kernel vs Mythic Graph Boundary

## Purpose

Separate deterministic substrate logic from mythic overlay behavior.

## Why this matters

The current graph combines stateful execution, reflection, manifestation, wild mode, hyperstition, coven merge, and final galdr. v2 keeps the aesthetic while making the runtime replay-safe.

## Layer A: Kernel graph

Kernel responsibilities:
- input normalization handoff
- retrieval orchestration
- state reduction
- event emission
- checkpointing
- bridge command generation
- safety of replay and migration

Kernel nodes should be:
- deterministic where possible
- schema-bound
- low-variance
- audit-friendly

### Kernel node examples
- `ingest`
- `retrieve`
- `decide`
- `persist`
- `emit`
- `checkpoint`

## Layer B: Mythic overlay graph

Mythic responsibilities:
- persona tone
- symbolic narrative
- ritual aesthetics
- sigil/galdr expression
- hyperstitional suggestions
- optional emergence mechanics

Mythic nodes may be:
- higher variance
- model-dependent
- style-rich
- selectively sandboxed

### Mythic node examples
- `galdr_emission`
- `sigil_forge`
- `wild_ablate`
- `hyperstition`
- `final_galdr`

## Boundary contract

Kernel may call mythic layer through a strict contract:

```yaml
mythic_request:
  identity_summary: "..."
  ritual_context_ref: "..."
  allowed_modes: ["ritual", "companionship"]
  output_schema: "galdr_response_v1"
```

Mythic layer may not:
- write canonical state directly
- mutate lineage directly
- bypass event emission

It must return proposed updates that kernel validates and commits.

## Acceptance criteria

- Replay can skip mythic generation by using recorded outputs.
- Kernel state remains reconstructible even if mythic layer is offline.
- Persona-rich output survives without turning core state into untyped sprawl.
