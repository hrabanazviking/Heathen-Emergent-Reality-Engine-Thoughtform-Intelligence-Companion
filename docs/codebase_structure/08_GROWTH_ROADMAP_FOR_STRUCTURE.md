# Growth Roadmap for Repository Structure

This roadmap keeps structure coherent while the project scales in depth and contributor count.

## Phase 1 — Canon Stabilization (Immediate)

- Keep all structure documents in `docs/codebase_structure/` updated.
- Add references from root `README.md` to this structure canon.
- Define required metadata headers for major architecture/spec documents.

## Phase 2 — Interface Visibility (Near-Term)

- Introduce `INTERFACE.md` files for major executable modules and service boundaries.
- Add folder-level `README_AI.md` files where missing.
- Ensure every protocol/spec file points to owning code or planned implementation location.

## Phase 3 — Data Taxonomy Hardening (Near-to-Mid)

- Establish consistent naming conventions for datasets.
- Add index manifests for high-volume directories.
- Create data provenance notes for critical cultural and lore corpora.

## Phase 4 — Cross-Layer Traceability (Mid-Term)

- Build explicit mapping tables:
  - principle -> spec -> module -> test
- Add architecture decision records (ADRs) for pivotal design choices.
- Improve schema validation and test coverage around memory/persona/protocol surfaces.

## Phase 5 — Operationalization (Mid-to-Long)

- Consolidate implementation-pack specs with runtime execution pathways.
- Add release-grade contributor and review checklists.
- Version structural canon with changelog entries.

## Definition of Structural Done

A structural change is complete only when:
1. the filesystem reflects the intended organization,
2. this document set is updated,
3. affected specs and tests remain aligned,
4. onboarding clarity improves instead of degrading.
