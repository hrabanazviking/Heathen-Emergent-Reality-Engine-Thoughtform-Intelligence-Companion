# Directory Contracts

This file defines what each major directory is for, what belongs there, and what must not be added there.

## Root (`/`)

**Contains**
- project identity docs
- legal/license artifacts
- core manifesto + architecture framing docs

**Rules**
- keep root readable: only high-signal canonical files
- avoid dumping intermediate notes in root

## `docs/codebase_structure/`

**Contains**
- repository structure canon
- organization maps and governance overlays

**Rules**
- markdown-only
- no executable code
- must stay synchronized with actual repository growth

## `data/`

**Contains**
- canonical datasets and static knowledge packs
- reference corpora for lore, culture, language, and style grounding

**Rules**
- prioritize durable formats (JSON, JSONL, YAML, MD)
- avoid transient generated noise
- preserve source quality and naming clarity

## `data/knowledge_reference/`

**Contains**
- extended reference library for cross-domain augmentation
- guidance, books, technical references, and thematic cultural source notes

**Rules**
- entries should be information-dense and non-duplicate
- maintain clear filenames and domain grouping

## `research_data/`

**Contains**
- engineering research docs
- reference architecture packets
- executable prototype modules and tests

**Rules**
- keep design docs and code aligned
- when adding code, add or update relevant tests
- preserve schema/spec consistency across docs and implementations

## `research_data/src/wyrdforge/`

**Contains**
- runtime models
- services and orchestration logic
- security and policy primitives
- schemas and protocol artifacts

**Rules**
- modular design
- explicit interfaces
- strict separation between data structures, services, and policies

## `research_data/tests/`

**Contains**
- automated checks for memory, persona, retrieval, and calibration paths

**Rules**
- every new behavior should have a corresponding test
- tests should encode expectations described by architecture docs

## `heretic_v2_implementation_pack/`

**Contains**
- v2 contracts/specifications for production-grade evolution

**Rules**
- specification-first structure
- each spec should define purpose, invariants, and integration touchpoints

## `proposed_system_report/`

**Contains**
- higher-level strategic and delivery planning artifacts

**Rules**
- keep report set coherent and version-consistent
- use this for macro planning, not implementation minutiae

## `data_project_development_resources/`

**Contains**
- external papers and references used for architecture inspiration and validation

**Rules**
- do not mix internal authoritative standards with external source documents
- keep citation-ready names where possible
