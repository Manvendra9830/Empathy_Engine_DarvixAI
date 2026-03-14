"""
app.py - Flask application entry-point for the Empathy Engine.

Routes
------
GET  /          – Renders the main UI (index.html).
POST /generate  – Accepts JSON {text}, runs the full pipeline, returns JSON
                  with emotion metadata and audio file paths.
GET  /health    – Simple health-check endpoint.
"""

from __future__ import annotations

import logging
import os

from flask import Flask, jsonify, render_template, request

import config
import utils
from emotion_detector import detect_emotion
from ssml_generator import build_ssml
from tts_engine import generate_audio_after, generate_audio_before
from voice_mapper import get_voice_params

# ── Logging setup ─────────────────────────────────────────────────────────────
utils.setup_logging(logging.INFO)
logger = logging.getLogger(__name__)

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1 MB request limit


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Render the main UI."""
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    """
    Full pipeline endpoint.

    Request body (JSON)
    -------------------
    { "text": "<user text>" }

    Response body (JSON)
    --------------------
    {
        "emotion":      "joy",
        "label":        "Joy / Positive",
        "emoji":        "😊",
        "color":        "#f9c74f",
        "confidence":   "87%",
        "pitch":        "+20%",
        "rate":         "fast",
        "volume":       "medium",
        "ssml":         "<speak>...</speak>",
        "all_scores":   [{label, score_pct}, ...],
        "audio_before": "/static/audio/audio-before.mp3?t=...",
        "audio_after":  "/static/audio/audio-after.mp3?t=...",
        "error":        null
    }
    """
    data = request.get_json(silent=True) or {}
    raw_text = data.get("text", "")

    # ── Input validation ───────────────────────────────────────────────────────
    text = utils.sanitise_text(raw_text)
    if not text:
        return jsonify({"error": "Please enter some text."}), 400

    try:
        # ── Step 1: Generate audio-before (plain TTS) ──────────────────────────
        before_path = os.path.join(app.static_folder, config.AUDIO_BEFORE_FILENAME)
        generate_audio_before(text, before_path)
        logger.info("audio-before generated.")

        # ── Step 2: Detect emotion ─────────────────────────────────────────────
        emotion, confidence, all_scores = detect_emotion(text)
        logger.info("Detected emotion=%s conf=%.2f", emotion, confidence)

        # ── Step 3: Map emotion → voice parameters ─────────────────────────────
        params = get_voice_params(emotion, confidence)

        # ── Step 4: Build SSML ────────────────────────────────────────────────
        ssml = build_ssml(text, params)

        # ── Step 5: Generate audio-after (emotion-aware) ───────────────────────
        after_path = os.path.join(app.static_folder, config.AUDIO_AFTER_FILENAME)
        generate_audio_after(text, params, after_path)
        logger.info("audio-after generated.")

        # ── Build response ─────────────────────────────────────────────────────
        bust = utils.cache_bust()
        return jsonify({
            "emotion":      emotion,
            "label":        params["label"],
            "emoji":        params["emoji"],
            "color":        params["color"],
            "confidence":   utils.format_confidence(confidence),
            "pitch":        params["pitch"],
            "rate":         params["rate"],
            "volume":       params["volume"],
            "ssml":         ssml,
            "all_scores":   utils.all_scores_to_sorted_list(all_scores),
            "audio_before": f"/static/{config.AUDIO_BEFORE_FILENAME}?t={bust}",
            "audio_after":  f"/static/{config.AUDIO_AFTER_FILENAME}?t={bust}",
            "error":        None,
        })

    except Exception as exc:
        logger.exception("Pipeline error: %s", exc)
        return jsonify({"error": f"An internal error occurred: {exc}"}), 500


@app.route("/health")
def health():
    """Simple liveness probe."""
    return jsonify({"status": "ok", "service": "empathy-engine"})


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Ensure the audio output directory exists before the first request
    utils.ensure_audio_dir(app.static_folder)
    logger.info(
        "Starting Empathy Engine on http://%s:%d",
        config.HOST, config.PORT
    )
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
