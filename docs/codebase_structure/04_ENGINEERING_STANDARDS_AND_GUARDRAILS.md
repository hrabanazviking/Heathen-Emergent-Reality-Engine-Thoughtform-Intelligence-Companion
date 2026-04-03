# Engineering Standards and Guardrails

This file consolidates engineering expectations into a practical codebase contract.

## 1) Documentation-First Delivery

- Every substantial technical change should include corresponding documentation updates.
- Structural changes must update `docs/codebase_structure/`.
- Spec changes should be reflected in tests when executable behavior exists.

## 2) Modularity and Internal API Discipline

- Prefer modules with single clear responsibility.
- Use internal interfaces between components rather than ad hoc cross-import coupling.
- Avoid circular dependency chains.

## 3) Data-Driven Design

- Put configurable values and domain content in data/config artifacts.
- Keep lore, cultural datasets, and symbolic references outside executable business logic.
- Preserve format diversity support (MD, JSON, JSONL, YAML, CSV, PDF ingestion references).

## 4) Fault-Tolerant Runtime Philosophy

- Build for resilience and graceful degradation.
- Treat runtime crashes as design failures unless explicitly unrecoverable.
- Log operational issues with enough detail for diagnosis.

## 5) Portability and Environment Agnosticism

- Avoid absolute paths.
- Keep modules location-agnostic within the repository.
- Favor cross-platform assumptions unless platform-specific behavior is deliberate and documented.

## 6) Additive Evolution

- Prefer additive upgrades that preserve compatibility.
- Avoid destructive rewrites that erase historical intent unless migration plans are explicit.
- Introduce versioned contracts for major behavior shifts.

## 7) Verification Expectations

- Add or update tests when implementing behavior in `research_data/src/wyrdforge/`.
- Keep schema and model changes synchronized.
- Validate that docs, tests, and implementations describe the same system.

## 8) Anti-Pattern Watchlist

- hardcoded lore or large static domain payloads in Python modules
- undocumented subsystem behavior
- deeply coupled modules with unclear boundaries
- one-off scripts becoming de facto production pathways without contracts
