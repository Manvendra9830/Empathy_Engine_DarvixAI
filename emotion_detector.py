"""
emotion_detector.py - Emotion classification using HuggingFace Transformers.

Loads a pre-trained DistilRoBERTa model fine-tuned on emotion data and
returns a normalised emotion label together with a confidence score.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Dict, Tuple

from transformers import pipeline

from config import EMOTION_MODEL_NAME, EMOTION_LABEL_MAP

logger = logging.getLogger(__name__)


# ── Model loader (cached so it is only loaded once per process) ───────────────

@lru_cache(maxsize=1)
def _get_classifier():
    """
    Load and cache the HuggingFace emotion-classification pipeline.
    Uses CPU by default; set device=0 to use GPU if available.
    """
    logger.info("Loading emotion model: %s", EMOTION_MODEL_NAME)
    clf = pipeline(
        task="text-classification",
        model=EMOTION_MODEL_NAME,
        top_k=None,          # return scores for all labels
        truncation=True,
        max_length=512,
    )
    logger.info("Emotion model loaded successfully.")
    return clf


# ── Public API ────────────────────────────────────────────────────────────────

def detect_emotion(text: str) -> Tuple[str, float, Dict[str, float]]:
    """
    Detect the dominant emotion in *text*.

    Parameters
    ----------
    text : str
        The input sentence(s) to classify.

    Returns
    -------
    emotion : str
        Normalised emotion label (one of the keys in EMOTION_VOICE_MAP).
    confidence : float
        Confidence score [0, 1] for the dominant label.
    all_scores : dict
        Mapping of *raw* model label → score for every class.
    """
    if not text or not text.strip():
        return "neutral", 1.0, {}

    classifier = _get_classifier()

    # pipeline returns [[{label, score}, ...]] when top_k=None
    results: list[dict] = classifier(text)[0]

    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)

    # Build raw scores dict
    all_scores: Dict[str, float] = {r["label"].lower(): r["score"] for r in results}

    # Pick the top raw label and normalise it
    raw_top_label = results[0]["label"].lower()
    confidence    = results[0]["score"]
    emotion       = EMOTION_LABEL_MAP.get(raw_top_label, "neutral")

    # Special heuristic: question marks often signal "inquisitive"
    if "?" in text and emotion in ("neutral", "joy"):
        emotion    = "inquisitive"
        confidence = max(confidence, 0.60)

    logger.debug(
        "Detected emotion=%s (raw=%s, conf=%.2f)",
        emotion, raw_top_label, confidence
    )
    return emotion, round(confidence, 4), all_scores
