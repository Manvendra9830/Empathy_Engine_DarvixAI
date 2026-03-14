"""
ssml_generator.py - Builds SSML markup from plain text + voice parameters.

SSML (Speech Synthesis Markup Language) gives us fine-grained control over
how a TTS engine renders speech.  This module wraps the user's text inside
<prosody> tags that encode pitch, rate, and volume, and optionally inserts
<break> pauses and <emphasis> markers.

Note: gTTS does NOT support SSML natively.  We therefore use SSML here as an
intermediate representation and apply the parameters programmatically when
calling the TTS engine (see tts_engine.py for the translation layer).
"""

from __future__ import annotations

import html
import logging
import re

logger = logging.getLogger(__name__)


def build_ssml(text: str, params: dict) -> str:
    """
    Generate an SSML string for the given text and voice parameters.

    Parameters
    ----------
    text : str
        Plain input text.
    params : dict
        Voice parameter dict from voice_mapper.get_voice_params().
        Expected keys: pitch, rate, volume, pause.

    Returns
    -------
    ssml : str
        Well-formed SSML string ready for a compliant TTS engine.

    Example output
    --------------
    <speak>
      <prosody pitch="+20%" rate="fast" volume="medium">
        This is amazing news!
      </prosody>
    </speak>
    """
    pitch  = params.get("pitch",  "default")
    rate   = params.get("rate",   "medium")
    volume = params.get("volume", "medium")
    pause  = params.get("pause",  0)          # ms

    # Escape any XML-special characters in the user text
    safe_text = html.escape(text.strip())

    # ── Optional: insert a short break after the first sentence ───────────────
    if pause > 0:
        safe_text = _insert_pause_after_first_sentence(safe_text, pause)

    # ── Optional: wrap exclamatory words in <emphasis> ─────────────────────────
    safe_text = _add_emphasis(safe_text, params)

    # ── Build prosody attributes ───────────────────────────────────────────────
    prosody_attrs = []
    if pitch != "default":
        prosody_attrs.append(f'pitch="{pitch}"')
    prosody_attrs.append(f'rate="{rate}"')
    if volume != "medium":
        prosody_attrs.append(f'volume="{volume}"')

    prosody_str = " ".join(prosody_attrs)

    ssml = (
        '<speak>\n'
        f'  <prosody {prosody_str}>\n'
        f'    {safe_text}\n'
        '  </prosody>\n'
        '</speak>'
    )

    logger.debug("Generated SSML:\n%s", ssml)
    return ssml


# ── Helpers ───────────────────────────────────────────────────────────────────

def _insert_pause_after_first_sentence(text: str, pause_ms: int) -> str:
    """
    Insert a <break> tag after the first sentence-ending punctuation.
    Falls back to inserting it after the first comma if no full stop is found.
    """
    # Match end of sentence: . ! ? followed by a space or end of string
    pattern = r'([.!?])(\s+|$)'
    replacement = rf'\1<break time="{pause_ms}ms"/>\2'
    modified, count = re.subn(pattern, replacement, text, count=1)
    if count == 0:
        # Fall back: insert after first comma
        modified = text.replace(",", f',<break time="{pause_ms}ms"/>', 1)
    return modified


def _add_emphasis(text: str, params: dict) -> str:
    """
    Wrap strongly emotional exclamatory words in <emphasis level="strong">.
    Only applied for high-energy emotions (joy, surprised, frustrated).
    """
    high_energy_emotions = {"joy", "surprised", "frustrated"}
    emotion = params.get("label", "").lower()

    # Check if any high-energy emotion keyword appears in the label
    is_high_energy = any(e in emotion for e in high_energy_emotions)
    if not is_high_energy:
        return text

    # Words that benefit from emphasis in high-energy speech
    emphasis_words = [
        "amazing", "incredible", "terrible", "awful", "fantastic",
        "wonderful", "horrible", "brilliant", "disastrous", "shocking",
    ]
    for word in emphasis_words:
        pattern = re.compile(rf'\b({re.escape(word)})\b', re.IGNORECASE)
        text = pattern.sub(r'<emphasis level="strong">\1</emphasis>', text)
    return text


def extract_plain_text_from_ssml(ssml: str) -> str:
    """
    Strip all SSML/XML tags from an SSML string and return plain text.
    Useful for logging or debug output.
    """
    clean = re.sub(r'<[^>]+>', '', ssml)
    clean = html.unescape(clean).strip()
    return clean
