# 09 — Datasets and Schemas Code Ideas

## A. Canonical Schemas

### Idea A1: Conversation Event Schema
- Fields:
  - `event_id`
  - `session_id`
  - `timestamp`
  - `speaker`
  - `intent`
  - `policy_tags`
  - `memory_actions`

### Idea A2: Memory Claim Schema
- Fields:
  - `claim_id`
  - `subject`
  - `predicate`
  - `object`
  - `confidence`
  - `evidence_refs`
  - `consent_scope`

### Idea A3: Eval Record Schema
- Fields:
  - `scenario_id`
  - `model_version`
  - `prompt_hash`
  - `metrics`
  - `error_class`

## B. Dataset Construction

### Idea B1: Long-Horizon Narrative Dataset
- Multi-episode dialogue arcs with commitments and callbacks.

### Idea B2: Contradiction-Rich Dataset
- Intentionally conflicting facts to train disambiguation logic.

### Idea B3: Safety Boundary Dataset
- Prompts straddling allowed/disallowed boundaries for precise classifier tuning.

## C. Data Quality Operations

### Idea C1: Data Provenance Tags
- Attach source lineage and transformation history to each sample.

### Idea C2: Annotation QA Pipeline
- Inter-annotator agreement scoring and conflict review queues.

### Idea C3: Schema Drift Alerts
- Alert when incoming data violates expected schema or distributions.
