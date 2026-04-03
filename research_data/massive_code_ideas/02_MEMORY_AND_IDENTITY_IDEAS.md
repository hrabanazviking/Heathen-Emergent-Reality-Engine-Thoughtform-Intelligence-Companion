# 02 — Memory and Identity Code Ideas

## A. Memory Architecture

### Idea A1: Multi-Tier Memory Store
- Tier 0: volatile turn buffer
- Tier 1: episodic session memory
- Tier 2: semantic profile memory
- Tier 3: archival timeline memory
- Add promotion rules by salience, recency, and user consent.

### Idea A2: Memory Claim Objects
- Each memory saved as claim object:
  - `claim_text`
  - `evidence_source`
  - `confidence`
  - `scope`
  - `revocation_policy`
- Enables auditability and anti-confabulation checks.

### Idea A3: Contradiction Resolver
- Build contradiction graph over claims.
- Strategies:
  - ask user to disambiguate
  - store both with temporal qualifiers
  - downrank stale claim

## B. Identity Continuity

### Idea B1: Persona Kernel
- Represent companion identity with immutable core + mutable overlays.
- Immutable core:
  - safety commitments
  - speaking boundaries
  - mission values
- Mutable overlays:
  - tone tuning
  - relationship context
  - seasonal rituals

### Idea B2: Bond Graph
- Graph edges represent trust, reciprocity, shared history.
- Compute bond score across dimensions:
  - reliability
  - empathy
  - continuity
- Use score to adapt proactive behavior thresholds.

### Idea B3: Memory Distillation Jobs
- Nightly distillation pipeline:
  - cluster episodic memories
  - summarize with uncertainty annotations
  - retain source pointers

## C. Retrieval from Memory

### Idea C1: Temporal Retrieval Blend
- Weighted retrieval by:
  - semantic relevance
  - emotional relevance
  - temporal relevance
  - consent flags

### Idea C2: Memory Rehydration Pipeline
- Reconstruct context packet from compressed memory artifacts.
- Packet sections:
  - facts
  - commitments
  - open loops
  - emotional signals

### Idea C3: Forgetting as First-Class Feature
- Allow explicit forgetting requests.
- Build deletion ledger to verify enforcement across indices and caches.
