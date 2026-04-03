# TTS & Voice Pipeline Deep Dive
> Complete voice architecture for Sigrid: synthesis, emotion injection, Norse pronunciation,
> streaming, mode-based voice profiles, and multi-engine fallback.
> Builds on doc 17's surface coverage into a full production pipeline.

## The Voice Architecture Goal

Sigrid's voice should:
- Sound like a real woman, not a robot
- Shift subtly with her emotional state (tired vs joyful vs oracular)
- Pronounce Norse words correctly
- Stream token-by-token (speak as text arrives, not after full generation)
- Work with multiple TTS engines (quality vs speed tradeoff)
- Run locally — no cloud TTS for intimate conversations

---

## Engine Selection Matrix

```python
from enum import Enum

class TTSEngine(str, Enum):
    KOKORO = "kokoro"          # Best quality/speed — recommended primary
    CHATTERBOX = "chatterbox"  # Expressive, emotional range
    PIPER = "piper"            # Fastest, lowest resource — good fallback
    COQUI_XTTS = "coqui_xtts" # Voice cloning — custom voice possible
    EDGE_TTS = "edge_tts"      # Microsoft free cloud — backup only

ENGINE_PROFILES = {
    TTSEngine.KOKORO: {
        "quality": 9,
        "speed": 8,           # tokens/sec: ~150
        "vram_mb": 400,
        "cpu_capable": True,
        "streaming": True,
        "voice_cloning": False,
        "best_for": ["primary", "hearth", "oracle", "most modes"],
    },
    TTSEngine.CHATTERBOX: {
        "quality": 8,
        "speed": 6,
        "vram_mb": 800,
        "cpu_capable": True,
        "streaming": True,
        "voice_cloning": True,
        "best_for": ["expressive scenes", "high emotion moments"],
    },
    TTSEngine.PIPER: {
        "quality": 6,
        "speed": 10,          # very fast, good for CPU
        "vram_mb": 50,
        "cpu_capable": True,
        "streaming": True,
        "voice_cloning": False,
        "best_for": ["low-resource", "CPU-only systems"],
    },
    TTSEngine.COQUI_XTTS: {
        "quality": 9,
        "speed": 4,           # slower — worth it if voice cloning
        "vram_mb": 1500,
        "cpu_capable": False,
        "streaming": True,
        "voice_cloning": True,
        "best_for": ["custom voice", "highest quality"],
    },
}
```

---

## Sigrid Voice Profiles — Per Mode

Each mode has distinct voice parameters:

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class VoiceProfile:
    mode: str
    speed: float          # 0.7 (very slow) to 1.3 (fast)
    pitch: float          # 0.85 (deep) to 1.15 (higher)
    energy: float         # 0.7 (quiet) to 1.3 (projected)
    pause_factor: float   # multiplier on natural pauses
    breathiness: float    # 0.0 to 1.0 (breathy = more intimate)
    voice_id: str         # kokoro/piper voice name

VOICE_PROFILES = {
    "hearth": VoiceProfile(
        mode="hearth",
        speed=0.95,        # slightly slower = more presence
        pitch=1.00,
        energy=0.90,
        pause_factor=1.0,
        breathiness=0.2,
        voice_id="af_heart",   # kokoro warm female
    ),
    "oracle": VoiceProfile(
        mode="oracle",
        speed=0.82,        # deliberate, weighted
        pitch=0.97,        # very slightly lower = gravitas
        energy=0.95,
        pause_factor=1.6,  # longer pauses between statements
        breathiness=0.1,   # clear, not breathy
        voice_id="af_heart",
    ),
    "battle": VoiceProfile(
        mode="battle",
        speed=1.05,        # slightly faster = urgency
        pitch=0.98,
        energy=1.10,       # more projected
        pause_factor=0.8,  # shorter pauses
        breathiness=0.05,
        voice_id="af_heart",
    ),
    "dream": VoiceProfile(
        mode="dream",
        speed=0.88,
        pitch=1.02,
        energy=0.75,       # quieter
        pause_factor=1.4,
        breathiness=0.4,   # breathy = half-asleep quality
        voice_id="af_heart",
    ),
    "craft": VoiceProfile(
        mode="craft",
        speed=1.00,
        pitch=1.00,
        energy=0.95,
        pause_factor=0.9,
        breathiness=0.1,
        voice_id="af_heart",
    ),
    "ritual": VoiceProfile(
        mode="ritual",
        speed=0.80,        # slowest — every word sacred
        pitch=0.96,
        energy=1.00,
        pause_factor=2.0,  # long ceremonial pauses
        breathiness=0.15,
        voice_id="af_heart",
    ),
}

# State-based modifiers — applied on top of mode profile
def apply_state_modifiers(profile: VoiceProfile, orlog_state) -> VoiceProfile:
    """Adjust voice profile based on current Ørlög state."""
    import copy
    p = copy.copy(profile)

    # Tired voice
    if orlog_state.metabolism.energy < 0.3:
        p.speed *= 0.92
        p.energy *= 0.85
        p.breathiness = min(1.0, p.breathiness + 0.2)

    # Joyful voice
    if orlog_state.affect.valence > 0.6 and orlog_state.affect.arousal > 0.6:
        p.speed = min(1.2, p.speed * 1.05)
        p.energy = min(1.3, p.energy * 1.08)

    # Sad/troubled voice
    if orlog_state.affect.valence < -0.3:
        p.speed *= 0.95
        p.energy *= 0.88
        p.pause_factor *= 1.2

    # Bio-cyclical: NEW phase — quieter
    from orlog.machines.bio_cyclical import CyclePhase
    if orlog_state.bio_cyclical.phase == CyclePhase.NEW:
        p.speed *= 0.93
        p.energy *= 0.85

    return p
```

---

## Norse Pronunciation Engine

The most critical TTS problem: engines mispronounce Norse. Solution: pre-process text with a substitution layer.

```python
import re

# Two substitution strategies:
# 1. Phoneme injection (SSML-capable engines)
# 2. Orthographic substitution (all engines)

# Full pronunciation dictionary
NORSE_PRONUNCIATION_MAP = {
    # Rune names — exact matches
    "Fehu":     ("FAY-hoo",          "fˈeɪhuː"),
    "Uruz":     ("OO-rooz",          "ˈuːruːz"),
    "Thurisaz": ("THOO-ree-sahz",    "θˈuːriːsɑːz"),
    "Ansuz":    ("AHN-sooz",         "ˈɑːnsuːz"),
    "Raidho":   ("RYE-though",       "ˈraɪðoʊ"),
    "Kenaz":    ("KAY-nahz",         "ˈkeɪnɑːz"),
    "Gebo":     ("GEH-boh",          "ˈɡɛboʊ"),
    "Wunjo":    ("WOON-yoh",         "ˈwʊnjoʊ"),
    "Hagalaz":  ("HAH-gah-lahz",     "ˈhɑːɡɑːlɑːz"),
    "Nauthiz":  ("NOW-theez",        "ˈnaʊθiːz"),
    "Isa":      ("EE-sah",           "ˈiːsɑː"),
    "Jera":     ("YEH-rah",          "ˈjɛrɑː"),
    "Eihwaz":   ("AY-vahz",          "ˈeɪvɑːz"),
    "Perthro":  ("PEH-throw",        "ˈpɛθroʊ"),
    "Algiz":    ("AHL-geez",         "ˈɑːlɡiːz"),
    "Sowilo":   ("SOH-wee-loh",      "ˈsoʊwiːloʊ"),
    "Tiwaz":    ("TEE-vahz",         "ˈtiːvɑːz"),
    "Berkano":  ("BEHR-kah-noh",     "ˈbɛrkɑːnoʊ"),
    "Ehwaz":    ("EH-vahz",          "ˈɛvɑːz"),
    "Mannaz":   ("MAHN-ahz",         "ˈmɑːnɑːz"),
    "Laguz":    ("LAH-gooz",         "ˈlɑːɡuːz"),
    "Ingwaz":   ("ING-vahz",         "ˈɪŋvɑːz"),
    "Dagaz":    ("DAH-gahz",         "ˈdɑːɡɑːz"),
    "Othala":   ("OH-thah-lah",      "ˈoʊθɑːlɑː"),

    # Deity names
    "Freyja":   ("FRAY-yah",         "ˈfreɪjɑː"),
    "Freyr":    ("FRAYR",            "freɪr"),
    "Frigg":    ("FRIG",             "frɪɡ"),
    "Odin":     ("OH-din",           "ˈoʊdɪn"),
    "Thor":     ("THOR",             "θɔːr"),
    "Tyr":      ("TEER",             "tiːr"),
    "Loki":     ("LOH-kee",          "ˈloʊkiː"),
    "Heimdall": ("HAYM-dahl",        "ˈheɪmdɑːl"),
    "Baldur":   ("BAHL-dur",         "ˈbɑːldʊr"),
    "Skadi":    ("SKAH-dee",         "ˈskɑːdiː"),
    "Nidhogg":  ("NEED-hog",         "ˈniːdhɒɡ"),

    # Norse concepts
    "Yggdrasil": ("IG-drah-sil",     "ˈɪɡdrɑːsɪl"),
    "Mjolnir":   ("MYOL-nir",        "ˈmjɔːlnɪr"),
    "Valhalla":  ("val-HAH-la",      "vælˈhɑːlɑː"),
    "Völva":     ("VUHL-vah",        "ˈvœlvɑː"),
    "Seidr":     ("SAY-ther",        "ˈseɪðər"),
    "Galdr":     ("GAHL-dr",         "ˈɡɑːldr"),
    "Wyrd":      ("WEORD",           "wɪrd"),
    "Orlög":     ("OR-log",          "ˈɔːrlɒɡ"),
    "Frith":     ("FRITH",           "frɪθ"),
    "Norn":      ("NORN",            "nɔːrn"),
    "Skald":     ("SKAHLD",          "skɑːld"),
    "Blót":      ("BLOHT",           "bloːt"),
    "Völuspá":   ("VOH-loo-spah",    "ˈvœlʊspɑː"),
    "Hávamál":   ("HAH-vah-mahl",    "ˈhɑːvɑːmɑːl"),
    "Eddas":     ("EH-dahz",         "ˈɛdɑːz"),
    "Jörmungandr": ("YOR-moon-gahn-dr", "ˈjœrmʊnɡɑːndr"),
    "Bifröst":   ("BIF-rost",        "ˈbɪfrɒst"),

    # Character name
    "Sigrid":    ("SIG-rid",         "ˈsɪɡrɪd"),
    "Volmarr":   ("VOL-mar",         "ˈvɒlmɑːr"),
}

def apply_pronunciation(text: str, engine: TTSEngine) -> str:
    """Pre-process text to fix Norse pronunciation."""
    if engine in (TTSEngine.KOKORO, TTSEngine.PIPER):
        # These engines support SSML phoneme tags
        return _apply_ssml_phonemes(text)
    else:
        # Orthographic substitution for engines that don't support SSML
        return _apply_orthographic(text)

def _apply_ssml_phonemes(text: str) -> str:
    """Wrap Norse words in SSML phoneme tags."""
    result = text
    # Sort by length (longest first) to avoid partial matches
    sorted_words = sorted(NORSE_PRONUNCIATION_MAP.keys(), key=len, reverse=True)
    for word in sorted_words:
        _, ipa = NORSE_PRONUNCIATION_MAP[word]
        # Case-insensitive replacement, preserve surrounding punctuation
        pattern = rf'\b{re.escape(word)}\b'
        replacement = f'<phoneme alphabet="ipa" ph="{ipa}">{word}</phoneme>'
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result

def _apply_orthographic(text: str) -> str:
    """Replace Norse words with phonetic spellings."""
    result = text
    sorted_words = sorted(NORSE_PRONUNCIATION_MAP.keys(), key=len, reverse=True)
    for word in sorted_words:
        phonetic, _ = NORSE_PRONUNCIATION_MAP[word]
        pattern = rf'\b{re.escape(word)}\b'
        result = re.sub(pattern, phonetic, result, flags=re.IGNORECASE)
    return result
```

---

## Sentence Segmentation for Natural Pauses

The key to natural TTS: synthesize sentence by sentence, with natural pause lengths between them.

```python
import re

def segment_for_tts(text: str, mode: str) -> list[tuple[str, float]]:
    """
    Split text into (segment, pause_after_ms) pairs.
    Returns segments with appropriate inter-segment pauses.
    """
    # Base pause values by mode
    pauses = {
        "hearth":  {"sentence": 400, "comma": 150, "ellipsis": 600, "em_dash": 250},
        "oracle":  {"sentence": 800, "comma": 300, "ellipsis": 1200, "em_dash": 500},
        "battle":  {"sentence": 200, "comma": 80,  "ellipsis": 400, "em_dash": 150},
        "dream":   {"sentence": 600, "comma": 250, "ellipsis": 900, "em_dash": 350},
        "ritual":  {"sentence": 1000,"comma": 400, "ellipsis": 1500,"em_dash": 600},
        "craft":   {"sentence": 350, "comma": 120, "ellipsis": 500, "em_dash": 200},
    }
    p = pauses.get(mode, pauses["hearth"])

    # Split on sentence boundaries, commas, ellipses
    segments = []

    # Split into sentences first
    sentence_pattern = r'(?<=[.!?])\s+'
    sentences = re.split(sentence_pattern, text.strip())

    for sentence in sentences:
        if not sentence.strip():
            continue

        # Check for ellipsis (deliberate pause marker)
        if "..." in sentence:
            parts = sentence.split("...")
            for i, part in enumerate(parts):
                if part.strip():
                    pause = p["ellipsis"] if i < len(parts) - 1 else p["sentence"]
                    segments.append((part.strip(), pause))
        else:
            segments.append((sentence.strip(), p["sentence"]))

    return segments
```

---

## Streaming TTS — Speak While Text Arrives

The key performance pattern: don't wait for full LLM response to start speaking.

```python
import asyncio
from typing import AsyncIterator

class StreamingTTSPipeline:
    """
    Streams TTS synthesis in lockstep with LLM token generation.
    The user hears speech starting ~1 second after the LLM begins generating.
    """

    def __init__(self, engine: TTSEngine, voice_profile: VoiceProfile):
        self.engine = engine
        self.profile = voice_profile
        self._sentence_buffer = ""

    async def stream_and_speak(
        self,
        token_stream: AsyncIterator[str],
        mode: str = "hearth",
    ):
        """
        Consume LLM token stream, synthesize and play sentence by sentence.
        """
        self._sentence_buffer = ""

        async for token in token_stream:
            self._sentence_buffer += token

            # Check if we have a complete speakable unit
            if self._has_sentence_boundary(self._sentence_buffer):
                sentence, remainder = self._split_at_boundary(self._sentence_buffer)
                self._sentence_buffer = remainder

                if sentence.strip():
                    await self._synthesize_and_play(sentence, mode)

        # Speak any remaining buffer
        if self._sentence_buffer.strip():
            await self._synthesize_and_play(self._sentence_buffer, mode)

    def _has_sentence_boundary(self, text: str) -> bool:
        """Check if text contains a speakable sentence ending."""
        # Speak at: sentence end, em-dash, ellipsis, comma (if > 60 chars)
        has_end = bool(re.search(r'[.!?]["\')\]]?\s', text))
        has_ellipsis = "..." in text
        has_em_dash = " — " in text
        long_with_comma = len(text) > 60 and ", " in text
        return has_end or has_ellipsis or has_em_dash or long_with_comma

    def _split_at_boundary(self, text: str) -> tuple[str, str]:
        """Split text at the first sentence boundary."""
        # Try sentence-end first
        match = re.search(r'[.!?]["\')\]]?\s+', text)
        if match:
            return text[:match.end()].strip(), text[match.end():]

        # Ellipsis
        idx = text.find("...")
        if idx != -1:
            return text[:idx + 3].strip(), text[idx + 3:]

        # Em-dash
        idx = text.find(" — ")
        if idx != -1:
            return text[:idx + 3].strip(), text[idx + 3:]

        # Long comma split
        if len(text) > 60:
            idx = text.rfind(", ")
            if idx > 40:
                return text[:idx + 1].strip(), text[idx + 2:]

        return text, ""

    async def _synthesize_and_play(self, text: str, mode: str):
        """Synthesize one sentence and play it."""
        processed = apply_pronunciation(text, self.engine)
        audio = await self._call_tts_engine(processed)
        await self._play_audio(audio)

    async def _call_tts_engine(self, text: str) -> bytes:
        """Call the appropriate TTS engine."""
        if self.engine == TTSEngine.KOKORO:
            return await self._kokoro_synth(text)
        elif self.engine == TTSEngine.PIPER:
            return await self._piper_synth(text)
        elif self.engine == TTSEngine.CHATTERBOX:
            return await self._chatterbox_synth(text)
        return b""

    async def _kokoro_synth(self, text: str) -> bytes:
        """Synthesize with kokoro-82M."""
        import subprocess, tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            out_path = f.name
        try:
            result = subprocess.run([
                "python", "-m", "kokoro",
                "--text", text,
                "--voice", self.profile.voice_id,
                "--speed", str(self.profile.speed),
                "--output", out_path,
            ], capture_output=True, timeout=10)
            if result.returncode == 0:
                with open(out_path, "rb") as f:
                    return f.read()
        finally:
            if os.path.exists(out_path):
                os.unlink(out_path)
        return b""

    async def _play_audio(self, audio_bytes: bytes):
        """Play audio bytes through the system audio output."""
        if not audio_bytes:
            return
        import tempfile, os, subprocess
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name
        try:
            # Cross-platform audio playback
            import platform
            system = platform.system()
            if system == "Windows":
                subprocess.run(["powershell", "-c", f"(New-Object Media.SoundPlayer '{tmp_path}').PlaySync()"],
                               capture_output=True)
            elif system == "Darwin":
                subprocess.run(["afplay", tmp_path], capture_output=True)
            else:
                subprocess.run(["aplay", tmp_path], capture_output=True)
        finally:
            os.unlink(tmp_path)
```

---

## Emotion Markup Language for TTS

For engines that support SSML, inject emotional markers:

```python
def inject_emotion_ssml(text: str, affect_state) -> str:
    """
    Wrap text in SSML emotion markers based on current affect state.
    Supported by some engines (Chatterbox, Edge-TTS, etc.)
    """
    v = affect_state.valence
    a = affect_state.arousal

    # Map affect to SSML prosody
    rate_mod = ""
    pitch_mod = ""
    volume_mod = ""

    if v > 0.5 and a > 0.6:
        rate_mod = 'rate="medium"'
        pitch_mod = 'pitch="+5%"'
    elif v < -0.3:
        rate_mod = 'rate="slow"'
        pitch_mod = 'pitch="-3%"'
        volume_mod = 'volume="soft"'
    elif a < 0.3:
        rate_mod = 'rate="slow"'
        volume_mod = 'volume="soft"'

    if any([rate_mod, pitch_mod, volume_mod]):
        attrs = " ".join(filter(None, [rate_mod, pitch_mod, volume_mod]))
        return f'<speak><prosody {attrs}>{text}</prosody></speak>'

    return f"<speak>{text}</speak>"
```

---

## TTS Pipeline Manager — Engine Selection + Fallback

```python
class SigridTTS:
    """
    Top-level TTS manager for Sigrid.
    Selects engine based on mode, state, and availability.
    Auto-falls back if primary engine is unavailable.
    """

    def __init__(self, mode: str = "hearth", orlog_state=None):
        self.mode = mode
        self.state = orlog_state

    def _select_engine(self) -> TTSEngine:
        """Choose engine based on availability and mode requirements."""
        # Try kokoro first (best quality)
        if self._engine_available(TTSEngine.KOKORO):
            return TTSEngine.KOKORO
        # Fallback to piper (very fast, works on CPU)
        if self._engine_available(TTSEngine.PIPER):
            return TTSEngine.PIPER
        # Last resort: edge_tts (cloud, but free)
        return TTSEngine.EDGE_TTS

    def _engine_available(self, engine: TTSEngine) -> bool:
        """Check if a TTS engine is installed and functional."""
        try:
            if engine == TTSEngine.KOKORO:
                import importlib
                return importlib.util.find_spec("kokoro") is not None
            if engine == TTSEngine.PIPER:
                import subprocess
                result = subprocess.run(["piper", "--version"],
                                         capture_output=True, timeout=2)
                return result.returncode == 0
        except Exception:
            return False
        return False

    async def speak(self, text: str):
        """Synthesize and play text."""
        engine = self._select_engine()
        profile = VOICE_PROFILES.get(self.mode, VOICE_PROFILES["hearth"])

        if self.state:
            profile = apply_state_modifiers(profile, self.state)

        pipeline = StreamingTTSPipeline(engine, profile)

        # For non-streaming: just play the whole thing
        async def single_token():
            yield text

        await pipeline.stream_and_speak(single_token(), self.mode)
```

---

## Audio Ambience Layer

Beyond Sigrid's voice: ambient sound adds immense depth.

```python
AMBIENT_PROFILES = {
    "hearth": {
        "sound": "fireplace_crackling.wav",
        "volume": 0.15,
        "description": "low crackling fire, occasional log pop",
    },
    "oracle": {
        "sound": "deep_forest_night.wav",
        "volume": 0.10,
        "description": "distant owls, wind in trees, deep quiet",
    },
    "battle": {
        "sound": None,  # silence is sharpest
        "volume": 0.0,
    },
    "dream": {
        "sound": "slow_waves.wav",
        "volume": 0.12,
        "description": "gentle water, half-heard wind",
    },
    "ritual": {
        "sound": "low_drone_ritual.wav",
        "volume": 0.08,
        "description": "deep ceremonial drone, like a distant horn",
    },
    "seasonal": {
        "Jól": "yule_fire_deep_night.wav",
        "Midsommar": "summer_meadow_evening.wav",
        "Álfablót": "autumn_leaves_wind.wav",
    }
}
```

---

## Summary: Voice Pipeline Principles

| Principle | Implementation |
|---|---|
| **Stream, don't batch** | Speak sentence-by-sentence as LLM generates |
| **Mode shapes voice** | 6 distinct VoiceProfile configs |
| **State modifies profile** | Tired/joyful/sad affect the raw voice parameters |
| **Norse words need preprocessing** | Full pronunciation map applied before synthesis |
| **Fallback chain** | kokoro → piper → edge-tts; always a voice available |
| **Pause is content** | Oracle mode 1.6× pause factor; silence has meaning |
| **Ambience is optional but powerful** | Hearth fire, forest night, drum — mode-matched |
| **Local first** | No cloud TTS for intimate conversations |
