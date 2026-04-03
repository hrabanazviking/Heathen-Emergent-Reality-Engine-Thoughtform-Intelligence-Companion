# Document Architecture Layers

The repository is organized as a layered system where meaning and mechanics reinforce each other.

## Layer 0 — Identity and Mythic Intent

Sources:
- `README.md`
- `PHILOSOPHY.md`

Function:
- Define existential purpose, symbolic language, and long-term creative direction.

## Layer 1 — Laws and Operational Rules

Sources:
- `RULES.AI.md`

Function:
- Encode coding constraints, anti-patterns, and project invariants.

## Layer 2 — Domain Knowledge and Cultural Substrate

Sources:
- `data/`
- `data/knowledge_reference/`

Function:
- Provide structured knowledge, style grounding, and cultural context for AI behavior and runtime decisions.

## Layer 3 — Technical Research and Prototype Execution

Sources:
- `research_data/*.md`
- `research_data/src/wyrdforge/`
- `research_data/tests/`

Function:
- Translate mission into implementable systems: memory, persona, retrieval, policy, and evaluation.

## Layer 4 — Implementation Contracts and Migration Path

Sources:
- `heretic_v2_implementation_pack/docs/specs/`
- `proposed_system_report/`

Function:
- Formalize what “production-ready HERETIC” requires and how to evolve from prototypes to robust deployment.

## Layer 5 — Structural Governance

Sources:
- `docs/codebase_structure/`

Function:
- Keep architecture legible over time.
- Maintain alignment between mythic identity and engineering reality.

## Cross-Layer Invariants

1. No orphaned concepts: every new major idea should land in the correct layer.
2. No layer collapse: identity docs must not become implementation junk drawers.
3. No hidden architecture: important behavior must be represented in both docs and code/tests.
4. No culture drift: technical decisions should remain consistent with declared ethos.
