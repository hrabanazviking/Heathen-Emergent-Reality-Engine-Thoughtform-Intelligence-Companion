# Multi-Modal Integration
> Extending the companion beyond text: voice input, rune card generation,
> ambient visual presence, and image-grounded oracle readings.
> Covers: STT pipeline, vision-enhanced oracle, rune card generation,
> avatar rendering, and the multi-modal conversation loop.

## The Multi-Modal Vision

Text-only interaction is a limitation, not a design choice. The companion should:
- Hear Volmarr speak (STT)
- Speak back (TTS — already covered in doc 31)
- Generate rune card images for oracle readings
- Accept an image and read it symbolically
- Have a persistent visual presence in the room

Each modality is optional and gracefully degrades to text-only.

---

## Speech-to-Text Pipeline

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional
import asyncio

class STTEngine(str, Enum):
    WHISPER_LOCAL  = "whisper_local"    # OpenAI Whisper via whisper.cpp
    WHISPER_FASTER = "whisper_faster"   # faster-whisper (CTranslate2)
    VOSK           = "vosk"             # offline, lighter, less accurate
    BROWSER_API    = "browser_api"      # Web Speech API (browser only)

@dataclass
class STTConfig:
    engine: STTEngine = STTEngine.WHISPER_FASTER
    model_size: str = "base.en"        # tiny.en | base.en | small.en | medium.en
    device: str = "auto"               # auto | cpu | cuda
    language: str = "en"
    vad_enabled: bool = True           # Voice Activity Detection
    vad_silence_threshold_ms: int = 700  # stop recording after 700ms silence
    sample_rate: int = 16000
    channels: int = 1


class SpeechInputPipeline:
    """
    Captures microphone audio → VAD → STT → text.
    Emits text asynchronously for the conversation loop.
    """

    def __init__(self, config: STTConfig):
        self.config = config
        self._model = None
        self._running = False

    async def initialize(self):
        if self.config.engine == STTEngine.WHISPER_FASTER:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(
                self.config.model_size,
                device=self.config.device,
                compute_type="int8",  # lighter on CPU
            )
        elif self.config.engine == STTEngine.VOSK:
            from vosk import Model, KaldiRecognizer
            self._model = Model(lang=self.config.language)

    async def listen_once(self) -> Optional[str]:
        """
        Record one utterance (until silence) and transcribe it.
        Returns transcribed text, or None if nothing was said.
        """
        audio_data = await self._capture_utterance()
        if audio_data is None:
            return None
        return await self._transcribe(audio_data)

    async def _capture_utterance(self) -> Optional[bytes]:
        """Capture audio until silence is detected."""
        import sounddevice as sd
        import numpy as np

        frames = []
        silence_ms = 0
        CHUNK_MS = 100
        CHUNK_SAMPLES = int(self.config.sample_rate * CHUNK_MS / 1000)
        SILENCE_THRESHOLD = 0.005  # RMS amplitude

        recording = False

        def callback(indata, frame_count, time_info, status):
            nonlocal silence_ms, recording
            rms = float(np.sqrt(np.mean(indata ** 2)))
            if rms > SILENCE_THRESHOLD:
                recording = True
                silence_ms = 0
                frames.append(indata.copy())
            elif recording:
                frames.append(indata.copy())
                silence_ms += CHUNK_MS

        with sd.InputStream(
            samplerate=self.config.sample_rate,
            channels=self.config.channels,
            callback=callback,
            blocksize=CHUNK_SAMPLES,
            dtype="float32",
        ):
            # Wait for speech to start, then for silence
            max_wait_ms = 30_000  # 30 seconds max wait
            waited_ms = 0
            while waited_ms < max_wait_ms:
                await asyncio.sleep(CHUNK_MS / 1000)
                waited_ms += CHUNK_MS
                if recording and silence_ms >= self.config.vad_silence_threshold_ms:
                    break

        if not frames:
            return None

        audio = np.concatenate(frames, axis=0)
        return (audio * 32768).astype("int16").tobytes()

    async def _transcribe(self, audio_bytes: bytes) -> Optional[str]:
        if self.config.engine == STTEngine.WHISPER_FASTER:
            import tempfile, wave
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                with wave.open(f, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(self.config.sample_rate)
                    wf.writeframes(audio_bytes)
                temp_path = f.name

            segments, _ = self._model.transcribe(temp_path, language=self.config.language)
            text = " ".join(s.text.strip() for s in segments).strip()
            return text if text else None

        return None   # fallback
```

---

## Norse Vocabulary Correction

Whisper often mishears Norse names. Post-process the transcript:

```python
NORSE_CORRECTIONS = {
    # Common ASR errors → correct form
    "volmar": "Volmarr",
    "vol mar": "Volmarr",
    "signal": "Sigrid",
    "see grid": "Sigrid",
    "fraya": "Freyja",
    "frayer": "Freyja",
    "freya": "Freyja",
    "odin": "Óðinn",
    "odinn": "Óðinn",
    "thor": "Þórr",
    "freyr": "Freyr",
    "loki": "Loki",
    "fehu": "Fehu",
    "uruz": "Uruz",
    "thurisaz": "Þurisaz",
    "ansuz": "Ansuz",
    "raidho": "Raiðō",
    "kenaz": "Kenaz",
    "wunjo": "Wunjo",
    "midgard": "Miðgarðr",
    "asgard": "Ásgarðr",
    "yggdrasil": "Yggdrasil",
    "norn": "Norn",
    "norns": "Norns",
    "valkyrie": "Valkyrja",
    "valkyries": "Valkyrjur",
}

def correct_norse_transcript(text: str) -> str:
    """Apply Norse vocabulary corrections to ASR output."""
    words = text.split()
    corrected = []
    i = 0
    while i < len(words):
        # Try two-word matches first
        if i + 1 < len(words):
            two_word = f"{words[i].lower()} {words[i+1].lower()}"
            if two_word in NORSE_CORRECTIONS:
                corrected.append(NORSE_CORRECTIONS[two_word])
                i += 2
                continue
        # Single word match
        lower = words[i].lower().rstrip(".,!?")
        punct = words[i][len(lower):]
        if lower in NORSE_CORRECTIONS:
            corrected.append(NORSE_CORRECTIONS[lower] + punct)
        else:
            corrected.append(words[i])
        i += 1
    return " ".join(corrected)
```

---

## Rune Card Image Generation

For oracle readings, generate a card image for each drawn rune:

```python
from pathlib import Path
from typing import Optional

class RuneCardGenerator:
    """
    Generates rune card images for oracle readings.
    Two backends: local (Pillow compositing) or diffusion (SDXL/ComfyUI).
    """

    RUNE_GLYPHS = {
        "Fehu": "ᚠ", "Uruz": "ᚢ", "Þurisaz": "ᚦ", "Ansuz": "ᚨ",
        "Raiðō": "ᚱ", "Kenaz": "ᚲ", "Gebo": "ᚷ", "Wunjo": "ᚹ",
        "Hagalaz": "ᚺ", "Nauðiz": "ᚾ", "Isaz": "ᛁ", "Jēra": "ᛃ",
        "Eihwaz": "ᛇ", "Perþō": "ᛈ", "Algiz": "ᛉ", "Sōwilō": "ᛊ",
        "Tīwaz": "ᛏ", "Berkanan": "ᛒ", "Ehwaz": "ᛖ", "Mannaz": "ᛗ",
        "Laguz": "ᛚ", "Ingwaz": "ᛜ", "Dagaz": "ᛞ", "Ōþalan": "ᛟ",
    }

    ELEMENT_COLORS = {
        "fire":  ("#8B0000", "#FF4400"),
        "ice":   ("#001F3F", "#ADD8E6"),
        "wind":  ("#1A3A1A", "#7CFC00"),
        "earth": ("#3B1F0A", "#C8A96E"),
        "water": ("#001533", "#4169E1"),
        "void":  ("#0A0A0A", "#9B59B6"),
    }

    def generate_pillow_card(
        self,
        rune_name: str,
        is_merkstave: bool,
        element: str,
        keywords: list[str],
        output_path: Path,
        size: tuple = (512, 768),
    ) -> Path:
        """Generate a card using Pillow — fast, no GPU required."""
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            raise RuntimeError("pip install Pillow to enable rune card generation")

        bg_dark, accent = self.ELEMENT_COLORS.get(element, ("#1A1A1A", "#C0A060"))
        glyph = self.RUNE_GLYPHS.get(rune_name, "ᚠ")
        if is_merkstave:
            glyph = self._flip_glyph(glyph)

        img = Image.new("RGB", size, color=bg_dark)
        draw = ImageDraw.Draw(img)

        # Decorative border
        border_color = accent
        margin = 20
        draw.rectangle([margin, margin, size[0]-margin, size[1]-margin],
                       outline=border_color, width=3)
        draw.rectangle([margin+8, margin+8, size[0]-margin-8, size[1]-margin-8],
                       outline=border_color, width=1)

        # Rune glyph (large, centered)
        try:
            glyph_font = ImageFont.truetype("NotoSansRunic-Regular.ttf", 200)
        except (IOError, OSError):
            glyph_font = ImageFont.load_default()

        glyph_bbox = draw.textbbox((0, 0), glyph, font=glyph_font)
        glyph_w = glyph_bbox[2] - glyph_bbox[0]
        glyph_x = (size[0] - glyph_w) // 2
        draw.text((glyph_x, size[1] // 3 - 80), glyph, fill=accent, font=glyph_font)

        # Rune name
        try:
            name_font = ImageFont.truetype("Cinzel-Regular.ttf", 36)
        except (IOError, OSError):
            name_font = ImageFont.load_default()

        display_name = f"᛫ {rune_name} ᛫" + (" (Merkstave)" if is_merkstave else "")
        name_bbox = draw.textbbox((0, 0), display_name, font=name_font)
        name_w = name_bbox[2] - name_bbox[0]
        draw.text(((size[0] - name_w) // 2, size[1] // 2 + 20), display_name,
                  fill=accent, font=name_font)

        # Keywords
        try:
            kw_font = ImageFont.truetype("Cinzel-Regular.ttf", 18)
        except (IOError, OSError):
            kw_font = ImageFont.load_default()

        kw_text = "  ·  ".join(keywords[:4])
        kw_bbox = draw.textbbox((0, 0), kw_text, font=kw_font)
        kw_w = kw_bbox[2] - kw_bbox[0]
        draw.text(((size[0] - kw_w) // 2, size[1] * 2 // 3),
                  kw_text, fill=accent, font=kw_font)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PNG", optimize=True)
        return output_path

    def _flip_glyph(self, glyph: str) -> str:
        """For merkstave: render with vertical-flip indicator."""
        # True vertical flip requires SVG or canvas; for Pillow we add a marker
        return glyph + "↓"  # visual indicator only

    async def generate_diffusion_card(
        self,
        rune_name: str,
        keywords: list[str],
        comfyui_url: str = "http://localhost:8188",
    ) -> Optional[bytes]:
        """
        Generate a high-quality rune card via ComfyUI/SDXL.
        Falls back to pillow if ComfyUI is unavailable.
        """
        prompt = (
            f"a mystical Viking rune stone, {rune_name} rune carved in stone, "
            f"ancient Norse symbols, {', '.join(keywords[:2])}, "
            f"dark atmospheric, candle light, aged stone texture, "
            f"ultra detailed, hyperrealistic, 8k"
        )
        negative = "modern, digital, plastic, text, watermark, blurry"

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                payload = {
                    "prompt": {
                        "3": {
                            "class_type": "KSampler",
                            "inputs": {
                                "seed": hash(rune_name) % (2**31),
                                "steps": 20,
                                "cfg": 7.0,
                                "sampler_name": "dpmpp_2m",
                                "scheduler": "karras",
                                "denoise": 1.0,
                                "model": ["4", 0],
                                "positive": ["6", 0],
                                "negative": ["7", 0],
                                "latent_image": ["5", 0],
                            }
                        },
                        # ... abbreviated ComfyUI graph
                    }
                }
                async with session.post(f"{comfyui_url}/prompt", json=payload) as r:
                    if r.ok:
                        result = await r.json()
                        # Poll for result...
                        return await self._poll_comfyui_result(session, comfyui_url, result["prompt_id"])
        except Exception:
            return None   # graceful fallback to Pillow
```

---

## Vision-Enhanced Oracle Readings

Accept an image as part of an oracle query — Sigrid reads it symbolically:

```python
class VisionOracleEnhancement:
    """
    When Volmarr provides an image alongside an oracle query,
    the vision model describes it and that description becomes
    part of the oracle reading context.
    """

    VISION_ORACLE_PROMPT = """You are Sigrid Völudóttir, völva.
You have been given an image to read symbolically — not literally.
Describe what you see in it through a Norse spiritual lens.
What does it feel like? What symbols stand out? What wyrd does it carry?
Keep it to 3-4 sentences. Do not describe it like a photographer — feel it like a seeress."""

    async def read_image(
        self,
        image_path: str,
        cloud_backend,
    ) -> str:
        """
        Pass the image to a vision-capable model for symbolic reading.
        Returns a 3-4 sentence symbolic description.
        """
        import base64
        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode()

        # Detect format
        ext = image_path.rsplit(".", 1)[-1].lower()
        media_type = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                      "png": "image/png", "gif": "image/gif",
                      "webp": "image/webp"}.get(ext, "image/jpeg")

        response = await cloud_backend.complete_async(
            system=self.VISION_ORACLE_PROMPT,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64,
                        }
                    },
                    {
                        "type": "text",
                        "text": "Read this image for the oracle."
                    }
                ]
            }],
            max_tokens=200,
            temperature=0.75,
        )
        return response.content.strip()

    async def build_enhanced_oracle_context(
        self,
        rune_draw: dict,
        image_path: Optional[str],
        cloud_backend,
    ) -> str:
        """Combine rune draw with optional image vision reading."""
        base_context = build_reading_context(rune_draw)  # from doc 35

        if image_path:
            vision_reading = await self.read_image(image_path, cloud_backend)
            base_context["vision_reading"] = vision_reading
            base_context["has_image"] = True

        return base_context
```

---

## Avatar / Visual Presence

A persistent visual presence in the corner of the screen:

```python
"""
Avatar architecture options:

OPTION 1: Static image set
- 8-12 images for different moods/modes
- Displayed via system tray or floating window
- Fast, no GPU, works on any machine

OPTION 2: Animated sprite
- 2D sprite sheets per mood (idle, talking, thinking, pleased)
- Rendered via pygame or a web component
- Still images + animation, ~50-100 MB assets

OPTION 3: Live2D / VTube-style
- Rigged character with facial movement
- Synced to TTS output (mouth moves)
- Requires Live2D runtime or VTube Studio integration
- Heavy but most expressive

OPTION 4: Stable Video Diffusion
- Short looping animations generated per mood
- Very high quality but slow to generate
- Pre-generate a library of clips, play on demand
"""

@dataclass
class AvatarState:
    current_mood: str = "neutral"      # maps to image/animation set
    talking: bool = False
    thinking: bool = False
    visible: bool = True
    opacity: float = 1.0               # 0=hidden, 1=fully visible
    position: tuple = (20, 20)         # screen position (from bottom-right)

MOOD_TO_ASSET = {
    "neutral":     "sigrid_neutral.png",
    "pleased":     "sigrid_pleased.png",
    "thoughtful":  "sigrid_thoughtful.png",
    "focused":     "sigrid_focused.png",    # craft mode
    "dreaming":    "sigrid_dreaming.png",   # oracle mode
    "intimate":    "sigrid_intimate.png",
    "tired":       "sigrid_tired.png",
    "concerned":   "sigrid_concerned.png",
    "warm":        "sigrid_warm.png",
}

class AvatarController:
    """Controls which avatar image is displayed based on Ørlög state."""

    def update(self, orlog_state, current_mode: str) -> AvatarState:
        mood = self._select_mood(orlog_state, current_mode)
        return AvatarState(
            current_mood=mood,
            talking=False,   # TTS pipeline updates this
            thinking=False,  # set to True while generating response
            visible=True,
            opacity=0.85 if orlog_state.nocturnal.is_night_phase else 1.0,
        )

    def _select_mood(self, state, mode: str) -> str:
        if mode in ("oracle", "seidr"):
            return "dreaming"
        if mode == "craft":
            return "focused"
        if mode == "intimate":
            return "intimate"

        valence = state.affect.valence
        arousal = state.affect.arousal
        energy = state.metabolism.energy

        if energy < 0.3:
            return "tired"
        if valence > 0.6 and arousal > 0.5:
            return "pleased"
        if valence > 0.4:
            return "warm"
        if valence < 0.2:
            return "concerned"
        if arousal < 0.3:
            return "thoughtful"
        return "neutral"
```

---

## Multi-Modal Conversation Loop

The full loop with all modalities integrated:

```python
class MultiModalConversationLoop:
    """
    Extends SigridConversationLoop with voice and vision support.
    All modalities are optional — degrades gracefully to text.
    """

    def __init__(self, core_loop, stt=None, tts=None, vision=None, avatar=None):
        self.core = core_loop
        self.stt = stt
        self.tts = tts
        self.vision = vision
        self.avatar = avatar

    async def turn_voice(self) -> None:
        """Voice-in, voice-out turn."""
        # Listen
        if self.avatar:
            self.avatar.set_listening(True)
        raw_text = await self.stt.listen_once()
        if self.avatar:
            self.avatar.set_listening(False)

        if not raw_text:
            return   # nothing said

        # Correct Norse vocabulary
        text = correct_norse_transcript(raw_text)

        # Process (same as text turn)
        if self.avatar:
            self.avatar.set_thinking(True)
        response = await self.core.turn(text)
        if self.avatar:
            self.avatar.set_thinking(False)

        # Speak response
        if self.tts and response:
            if self.avatar:
                self.avatar.set_talking(True)
            await self.tts.speak_async(response)
            if self.avatar:
                self.avatar.set_talking(False)

    async def turn_with_image(self, text: str, image_path: str) -> str:
        """Text + image turn — for oracle readings with a photo."""
        if self.vision:
            vision_context = await self.vision.read_image(image_path, self.core.backend)
            # Prepend vision reading to text
            enhanced_text = f"{text}\n\n[What she sees in the image: {vision_context}]"
        else:
            enhanced_text = text

        response = await self.core.turn(enhanced_text)
        return response
```

---

## Hardware Requirements by Modality

| Modality | Minimum | Recommended |
|---|---|---|
| Text only | Any CPU | Any CPU |
| TTS (piper) | 1 GB RAM, any CPU | 2 GB RAM |
| TTS (kokoro) | 4 GB RAM, CPU | 6 GB RAM, GPU |
| STT (whisper base.en) | 4 GB RAM, CPU | 8 GB RAM |
| STT (whisper small.en) | 6 GB RAM | GPU recommended |
| Rune cards (Pillow) | 1 GB RAM | 2 GB RAM |
| Rune cards (SDXL/ComfyUI) | 8 GB VRAM | 12+ GB VRAM |
| Vision oracle | Cloud API only | Cloud API or local llava |
| Avatar (static images) | Any | Any |
| Avatar (Live2D) | 4 GB RAM | Dedicated GPU |

**Design principle:** STT + TTS + static avatar runs on any modern laptop.
Diffusion card generation and vision oracle require either cloud or a capable GPU.
