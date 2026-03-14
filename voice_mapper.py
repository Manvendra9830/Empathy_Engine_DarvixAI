"""
voice_mapper.py - Maps a detected emotion to a set of SSML vocal parameters.

This module is intentionally thin: it simply looks up the emotion in the
EMOTION_VOICE_MAP config and returns the corresponding parameter dict.
Keeping mapping logic isolated makes it easy to tune without touching other
modules.
"""

from __future__ import annotations

import logging
from typing import Dict

from config import EMOTION_VOICE_MAP

logger = logging.getLogger(__name__)


def get_voice_params(emotion: str, confidence: float = 1.0) -> Dict:
    """
    Return vocal parameters for the given *emotion*.

    Parameters
    ----------
    emotion : str
        Normalised emotion label (must be a key in EMOTION_VOICE_MAP).
    confidence : float
        Detection confidence [0, 1].  Used for *intensity scaling*:
        at confidence < 0.55 the parameters are blended toward neutral so that
        low-confidence predictions don't produce jarring speech.

    Returns
    -------
    params : dict
        A copy of the voice parameter dict with keys:
        pitch, rate, volume, pause, label, emoji, color.
    """
    params = dict(EMOTION_VOICE_MAP.get(emotion, EMOTION_VOICE_MAP["neutral"]))

    # ── Intensity scaling ──────────────────────────────────────────────────────
    # When confidence is below the threshold, soften the pitch modulation so
    # that borderline detections don't sound over-the-top.
    CONFIDENCE_THRESHOLD = 0.55
    if confidence < CONFIDENCE_THRESHOLD and params["pitch"] not in ("default",):
        try:
            pct_str = params["pitch"]          # e.g. "+20%"
            sign    = 1 if pct_str[0] == "+" else -1
            value   = float(pct_str.replace("%", "").replace("+", "").replace("-", ""))
            # Scale down by the ratio of confidence to threshold
            scaled  = value * (confidence / CONFIDENCE_THRESHOLD)
            params["pitch"] = f"{'+' if sign > 0 else '-'}{scaled:.0f}%"
        except (ValueError, IndexError):
            pass  # If parsing fails just keep the original value

    logger.debug(
        "Voice params for emotion=%s (conf=%.2f): %s",
        emotion, confidence, params
    )
    return params
