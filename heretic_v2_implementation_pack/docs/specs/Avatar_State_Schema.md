# Avatar State Schema

## Purpose

Define the runtime state mirrored into a 3D avatar.

## Schema

```yaml
avatar_id: "avatar_uuid"
thoughtform_id: "tf_uuid"
session_id: "session_uuid"
expression:
  valence: 0.2
  arousal: 0.7
  gaze_target: "camera|user|offscreen"
  blink_rate: 0.12
gesture:
  stance: "neutral|ritual|approach|withdraw"
  hand_state: "open|point|sigil"
  locomotion: "idle|step|turn"
visual_fx:
  rune_glow_intensity: 0.66
  ghost_glow_intensity: 0.10
  particle_mode: "off|ritual|superposition"
audio_sync:
  speaking: true
  phoneme_stream_ref: "audio://..."
health:
  degraded_mode: false
  last_sync_latency_ms: 18
```

## Boundaries

- Avatar state is expressive, not canonical.
- It may be regenerated from canonical + bridge context.
- It may not independently mutate lineage, memory, or identity.

## Acceptance criteria

- Avatar can recover after disconnect using latest valid state message.
- Expression mismatches can be measured against generated content.
