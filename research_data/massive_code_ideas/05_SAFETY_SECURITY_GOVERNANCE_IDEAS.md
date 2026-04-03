# 05 — Safety, Security, and Governance Code Ideas

## A. Safety Enforcement

### Idea A1: Layered Policy Engine
- Stage gates:
  - pre-plan policy checks
  - pre-tool execution checks
  - pre-response output checks
- Track every policy decision in auditable logs.

### Idea A2: Consent State Machine
- Explicit consent states for memory use, proactive contact, and sensitive topics.
- Refuse transitions without user-confirmed events.

### Idea A3: Emotional Safety Guardrails
- Detect potential overdependence cues.
- Route response style to grounding and autonomy-supporting language.

## B. Security Architecture

### Idea B1: Tool Risk Segmentation
- Group tools by blast radius:
  - low: read-only helpers
  - medium: bounded file writes
  - high: external side effects
- Enforce extra confirmations by class.

### Idea B2: Prompt Injection Firewall
- Add detector chain:
  - instruction conflict detection
  - data exfiltration pattern matching
  - command escalation detection

### Idea B3: Secrets Minimization
- Use ephemeral credentials with short TTL.
- Never expose raw secrets to model context.

## C. Governance

### Idea C1: Incident Replay Bundle
- Automatically package:
  - trace
  - prompts
  - tool I/O
  - policy decisions
- Speeds postmortems and governance review.

### Idea C2: Model Behavior Ledger
- Version behavior policies and prompt templates.
- Associate every response with active policy hash.

### Idea C3: Safety Eval Gates in CI/CD
- Block deployment if safety regression exceeds thresholds.
