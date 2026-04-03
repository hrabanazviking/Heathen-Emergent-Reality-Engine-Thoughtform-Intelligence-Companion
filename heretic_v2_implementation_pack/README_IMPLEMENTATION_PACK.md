# H.E.R.E.T.I.C. v2 Implementation Pack

This pack contains a concrete v2 specification layer for H.E.R.E.T.I.C.

The design intent is to preserve the existing H.E.R.E.T.I.C. vision while making the system:
- replayable
- versioned
- testable
- observable
- modular

## Guiding decisions

1. **Event log is the canonical truth**
   - Runtime stores are projections and caches.
   - Chroma, Neo4j, and Redis are no longer peers; they are specialized views over the same canonical history.

2. **Kernel and mythic logic are separated**
   - Kernel nodes are deterministic, auditable, and replay-safe.
   - Mythic overlay nodes shape persona, ritual aesthetics, symbolic language, and emergence.

3. **Latency is tiered**
   - Hot path: avatar responsiveness and emotional mirroring
   - Warm path: dialogue and ritual turn generation
   - Cold path: reflection, memory consolidation, art generation, evolution

4. **Ghost echoes become a first-class subsystem**
   - Non-selected futures are queryable, compressible, and reusable during mutation or resurrection.

5. **Every major claim gets an eval**
   - Identity continuity
   - Memory grounding
   - Resurrection fidelity
   - Bridge fidelity
   - Drift containment
   - Multi-thoughtform permissions

## Recommended application order

1. Freeze contracts and schemas
2. Implement event ledger and replay
3. Convert memory backends into projections
4. Split graph into kernel and mythic layers
5. Add eval harness and observability
6. Harden coven and lineage mechanics

## Pack contents

### Core substrate
- `Thoughtform_State_Schema_v2.md`
- `Event_Ledger_Architecture.md`
- `Canonical_Event_Types.md`
- `Replay_and_Resurrection.md`
- `State_Migration_Strategy.md`

### Runtime / graph
- `Kernel_vs_Mythic_Graph_Boundary.md`
- `Node_Taxonomy_v2.md`
- `Router_Policy_v2.md`
- `Collapse_and_Superposition_Guardrails.md`

### Memory
- `Memory_Projection_Model.md`
- `Ghost_Echo_Model.md`
- `Alternate_Futures_Queries.md`
- `Memory_Retention_and_Compaction.md`

### Bridge / interaction
- `Bridge_Message_Contracts.md`
- `Avatar_State_Schema.md`
- `Ritual_Session_Protocol.md`

### Reliability / measurement
- `SLO_Tiers.md`
- `Eval_Harness_v1.md`
- `Continuity_Eval_Set.md`
- `Resurrection_Fidelity_Evals.md`
- `Observability_Model.md`

### Multi-user / lineage
- `Coven_Permissions_Model.md`
- `Shared_Ritual_State.md`
- `Merge_and_Fork_Lineage.md`

## Suggested repo placement

```text
heretic/
├── docs/
│   └── specs/
├── core/
│   ├── kernel/
│   ├── agents/
│   ├── memory/
│   ├── ritual/
│   └── schemas/
├── manifestation/
├── evals/
└── observability/
```
