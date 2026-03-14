"""
utils.py - Shared utility helpers for the Empathy Engine.
"""

from __future__ import annotations

import logging
import os
import re
import time
from pathlib import Path


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger with a human-friendly format."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )


def sanitise_text(text: str) -> str:
    """
    Basic sanity-check / cleanup on user-supplied text.

    - Strip leading/trailing whitespace.
    - Collapse internal runs of whitespace to a single space.
    - Limit length to 1 000 characters to avoid excessive TTS costs.
    """
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    if len(text) > 1000:
        text = text[:1000] + "…"
    return text


def ensure_audio_dir(static_folder: str) -> str:
    """
    Create the static/audio directory if it does not exist and return its path.
    """
    audio_dir = os.path.join(static_folder, "audio")
    Path(audio_dir).mkdir(parents=True, exist_ok=True)
    return audio_dir


def cache_bust() -> str:
    """
    Return a short cache-busting token (current Unix timestamp).
    Append to audio src URLs so the browser doesn't play stale cached files.
    """
    return str(int(time.time()))


def format_confidence(confidence: float) -> str:
    """Return a human-readable confidence string, e.g. '87%'."""
    return f"{confidence * 100:.0f}%"


def all_scores_to_sorted_list(raw_scores: dict) -> list[dict]:
    """
    Convert raw model score dict to a list of dicts sorted by score descending.
    Each item: {label, score_pct}
    """
    return [
        {"label": k.title(), "score_pct": f"{v * 100:.1f}"}
        for k, v in sorted(raw_scores.items(), key=lambda x: x[1], reverse=True)
    ]
