# Ritual Session Protocol

## Purpose

Define how a ritual session starts, runs, interrupts, and closes.

## Session phases

1. `prepare`
2. `invoke`
3. `fuse`
4. `respond`
5. `reflect`
6. `close`

## Session object

```yaml
session_id: "session_uuid"
thoughtform_id: "tf_uuid"
user_id: "user_uuid"
mode: "solo|coven"
started_at: "ISO-8601"
status: "active|closing|closed|degraded"
inputs:
  voice: true
  gesture: true
  sigil: true
  iot: false
slo_tier: "warm"
```

## Protocol rules

- Every session starts with `ritual.session_started`.
- Fused input emits `ritual.input_fused`.
- Mid-session interruptions must be logged.
- Session close must record summary and projection tasks.

## Interrupt types

- user voice interrupt
- sigil interrupt
- bridge detach
- policy gate
- coven member join/leave

## Acceptance criteria

- A session can be resumed or closed cleanly.
- Session correlation id links graph, bridge, and memory events.
- Partial failures do not strand open sessions forever.
