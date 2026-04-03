# Bridge Message Contracts

## Purpose

Define stable contracts between Python runtime and 3D manifestation layers such as Unity or WebGL.

## Channels

- `bridge.avatar.state`
- `bridge.pose.delta`
- `bridge.audio.cue`
- `bridge.session.control`
- `bridge.health`

## Envelope

```json
{
  "schema": "bridge.avatar.state.v1",
  "seq": 182,
  "thoughtform_id": "tf_uuid",
  "session_id": "session_uuid",
  "ts": "2026-04-02T20:10:00Z",
  "payload": {}
}
```

## Required schemas

### `bridge.avatar.state.v1`
Contains emotional tags, animation intent, expression weights, rune glow parameters.

### `bridge.pose.delta.v1`
Small pose updates optimized for hot path.

### `bridge.audio.cue.v1`
Phoneme timing, intensity, and sync markers.

### `bridge.session.control.v1`
Connect, pause, resume, detach, text-only fallback.

## Rules

1. Bridge messages must be versioned independently from canonical state.
2. Bridge loss must not corrupt canonical thoughtform state.
3. Seq values must be monotonic within a session.
4. Text-only fallback must be supported.

## Acceptance criteria

- Unity/WebGL runtimes can ignore unknown future fields safely.
- Hot-path pose and expression messages are compact.
- Operators can inspect raw bridge traffic by session id.
