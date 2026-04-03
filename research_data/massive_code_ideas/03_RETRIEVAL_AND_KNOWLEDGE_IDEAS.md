# 03 — Retrieval and Knowledge Code Ideas

## A. Multi-Scale Retrieval

### Idea A1: Retrieval Pyramid
- Layered retrieval stages:
  1. lexical prefilter
  2. embedding candidate fetch
  3. graph-neighborhood expansion
  4. reranker with citation utility score

### Idea A2: Micro-RAG for Small Models
- Build compact retrieval packets:
  - max 3 facts
  - max 2 source anchors
  - one uncertainty note
- Goal: raise answer precision while preserving token budget.

### Idea A3: Query Decomposition Engine
- Break user request into sub-queries:
  - factual
  - procedural
  - preference-based
- Route each to fitting retrieval adapters.

## B. Knowledge Graph Ideas

### Idea B1: Wyrd Knowledge Mesh
- Hybrid graph with entity, relation, event, and ritual nodes.
- Add provenance edges from source documents.

### Idea B2: Belief State Overlay
- Separate:
  - world facts
  - user beliefs
  - agent hypotheses
- Avoids conflating uncertain inference with stable fact.

### Idea B3: Citation-First Generation
- Generation policy requires citation plan before drafting answer.
- Fail closed to “insufficient evidence” when sources are weak.

## C. Truth Calibration

### Idea C1: Confidence Envelope
- Include confidence bands in internal reasoning state.
- Trigger clarification if confidence below threshold.

### Idea C2: Adversarial Retrieval Checks
- Before final response:
  - retrieve contradiction candidates
  - retrieve policy conflict candidates
- Reject fragile claims.

### Idea C3: Source Freshness Policy
- Apply recency windows per domain:
  - prices/news: hours to days
  - standards/docs: weeks to months
  - foundational references: longer horizon
