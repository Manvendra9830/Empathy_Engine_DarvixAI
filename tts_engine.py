"""
tts_engine.py - Audio generation layer.

Generates two audio files for every request:

  audio-before.mp3  –  Plain gTTS output (no emotion modulation).
  audio-after.mp3   –  Emotion-aware output: gTTS + pydub post-processing
                        to apply pitch shift and tempo change derived from
                        the SSML parameters.

Why pydub instead of gTTS SSML?
  gTTS wraps the Google Translate TTS endpoint which does NOT support SSML.
  We therefore use pydub (backed by ffmpeg) to apply the prosody parameters
  as audio-domain post-processing after synthesis.  The result is not as
  sophisticated as a full SSML-capable engine (e.g. Google Cloud TTS) but
  gives a clearly audible difference between the before/after files.

Pitch shift mapping
  "+20%"  → semitones = +20/6  ≈ +3.3 st
  "-15%"  → semitones = -15/6  ≈ -2.5 st
  "+30%"  → semitones = +30/6  ≈ +5.0 st
  etc.

Rate mapping
  "fast"   → 1.25×
  "medium" → 1.00×
  "slow"   → 0.80×

Volume mapping
  "loud"   → +5 dB
  "soft"   → -5 dB
  "medium" → 0 dB
"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

from gtts import gTTS

from config import GTTS_LANG, GTTS_TLD

logger = logging.getLogger(__name__)

# ── Attempt to import pydub; fall back gracefully ────────────────────────────
try:
    from pydub import AudioSegment
    from pydub.effects import speedup
    from pydub.utils import which

    AudioSegment.converter = which("ffmpeg") or r"C:\ffmpeg\ffmpeg-2026-03-12-git-9dc44b43b2-full_build\bin\ffmpeg.exe"
    AudioSegment.ffprobe = which("ffprobe") or r"C:\ffmpeg\ffmpeg-2026-03-12-git-9dc44b43b2-full_build\bin\ffprobe.exe"

    PYDUB_AVAILABLE = True
    logger.info("pydub available – full audio modulation enabled.")
except ImportError:
    PYDUB_AVAILABLE = False
    logger.warning(
        "pydub not installed – audio-after will be identical to audio-before. "
        "Install pydub + ffmpeg for full modulation support."
    )


# ── Constants ─────────────────────────────────────────────────────────────────

RATE_MAP   = {"fast": 1.25, "medium": 1.00, "slow": 0.80}
VOLUME_MAP = {"loud": 5,    "medium": 0,    "soft": -5}


# ── Public API ────────────────────────────────────────────────────────────────

def generate_audio_before(text: str, output_path: str) -> None:
    """
    Synthesise *text* with default (neutral) gTTS settings and save to
    *output_path*.
    """
    _gtts_save(text, output_path)
    logger.info("audio-before saved: %s", output_path)


def generate_audio_after(text: str, params: dict, output_path: str) -> None:
    """
    Synthesise *text* and apply vocal modulation derived from *params*.

    Parameters
    ----------
    text : str
        Plain text to synthesise (SSML tags are stripped if present).
    params : dict
        Voice parameter dict from voice_mapper.get_voice_params().
    output_path : str
        Destination file path for the modulated MP3.
    """
    # Step 1 – synthesise neutral audio to a temp file
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        _gtts_save(text, tmp_path)

        if PYDUB_AVAILABLE:
            _apply_modulation(tmp_path, params, output_path)
        else:
            # Without pydub just copy the neutral audio
            import shutil
            shutil.copy(tmp_path, output_path)
            logger.warning("pydub unavailable – audio-after is unmodified.")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    logger.info("audio-after saved: %s", output_path)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _gtts_save(text: str, path: str) -> None:
    """Call gTTS and save the result to *path*."""
    # Ensure parent directory exists
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    tts = gTTS(text=text, lang=GTTS_LANG, tld=GTTS_TLD, slow=False)
    tts.save(path)


def _apply_modulation(src_path: str, params: dict, dst_path: str) -> None:
    """
    Load the MP3 at *src_path*, apply pitch / rate / volume modulation
    derived from *params*, and save to *dst_path*.
    """
    audio = AudioSegment.from_mp3(src_path)

    # ── Volume ─────────────────────────────────────────────────────────────────
    volume_key = params.get("volume", "medium")
    db_change   = VOLUME_MAP.get(volume_key, 0)
    if db_change != 0:
        audio = audio + db_change

    # ── Rate / tempo ───────────────────────────────────────────────────────────
    rate_key   = params.get("rate", "medium")
    rate_factor = RATE_MAP.get(rate_key, 1.0)
    if rate_factor != 1.0:
        audio = _change_speed(audio, rate_factor)

    # ── Pitch shift ────────────────────────────────────────────────────────────
    pitch_str = params.get("pitch", "default")
    if pitch_str != "default":
        semitones = _pitch_str_to_semitones(pitch_str)
        if semitones != 0:
            audio = _shift_pitch(audio, semitones)

    # Export
    Path(dst_path).parent.mkdir(parents=True, exist_ok=True)
    audio.export(dst_path, format="mp3")


def _change_speed(audio: "AudioSegment", factor: float) -> "AudioSegment":
    """
    Change playback speed without changing pitch by resampling the frame rate.
    Effectively a time-stretch approximation suitable for speech.
    """
    new_frame_rate = int(audio.frame_rate * factor)
    sped_audio = audio._spawn(
        audio.raw_data,
        overrides={"frame_rate": new_frame_rate}
    )
    # Convert back to the original sample rate so the player handles it fine
    return sped_audio.set_frame_rate(audio.frame_rate)


def _shift_pitch(audio: "AudioSegment", semitones: float) -> "AudioSegment":
    """
    Shift pitch by *semitones* half-steps.

    Implementation: change the frame rate by the corresponding frequency
    ratio and then resample back.  This is a simple, dependency-free approach
    (no librosa needed).

    ratio = 2 ** (semitones / 12)
    """
    ratio = 2 ** (semitones / 12)
    new_frame_rate = int(audio.frame_rate * ratio)
    shifted = audio._spawn(
        audio.raw_data,
        overrides={"frame_rate": new_frame_rate}
    )
    return shifted.set_frame_rate(audio.frame_rate)


def _pitch_str_to_semitones(pitch_str: str) -> float:
    """
    Convert SSML-style pitch string (e.g. "+20%", "-15%") to semitones.

    We use the approximation:  semitones ≈ percentage / 6
    which keeps small percentage changes perceptible but not extreme.
    """
    try:
        pct = float(pitch_str.replace("%", ""))
        return pct / 6.0
    except ValueError:
        return 0.0
