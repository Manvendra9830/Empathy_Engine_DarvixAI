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
    Return vocal parameters for the given *emotion*, scaled by detection confidence.

    Parameters
    ----------
    emotion : str
        Normalised emotion label (must be a key in EMOTION_VOICE_MAP).
    confidence : float
        Detection confidence [0, 1]. Used for intensity scaling:
        pitch = base_pitch * confidence
        rate = base_rate * confidence

    Returns
    -------
    params : dict
        A copy of the voice parameter dict with scaled pitch/rate as strings.
    """
    config_params = EMOTION_VOICE_MAP.get(emotion, EMOTION_VOICE_MAP["neutral"])
    
    # Create a copy so we don't modify the original config
    params = dict(config_params)

    # ── Confidence-based Intensity Scaling ─────────────────────────────────────
    # Multiply numeric base values by confidence and format as SSML strings
    pitch_scaled = params["pitch"] * confidence
    rate_scaled  = params["rate"] * confidence

    # Update params with formatted strings e.g. "+6.5%"
    params["pitch"] = f"{pitch_scaled:+.1f}%"
    params["rate"]  = f"{rate_scaled:+.1f}%"

    logger.debug(
        "Scaled voice params for emotion=%s (conf=%.2f): pitch=%s, rate=%s",
        emotion, confidence, params["pitch"], params["rate"]
    )
    return params
