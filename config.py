"""
config.py - Central configuration for the Empathy Engine
Research-based emotional prosody mapping
"""

# ── HuggingFace model ─────────────────────────────────────────────
EMOTION_MODEL_NAME = "j-hartmann/emotion-english-distilroberta-base"

# ── Emotion label normalisation ───────────────────────────────────
EMOTION_LABEL_MAP = {
    "joy":      "joy",
    "neutral":  "neutral",
    "anger":    "frustrated",
    "disgust":  "frustrated",
    "sadness":  "concerned",
    "fear":     "concerned",
    "surprise": "surprised",
}

# ── Voice parameter mapping ────────────────────────────────────────────────────
# pitch  : Numeric base value in percentage (scaled by confidence)
# rate   : Numeric base value in percentage (scaled by confidence)
# volume : SSML prosody value  e.g. "loud", "soft", "medium"
# pause  : milliseconds inserted after the first sentence (adds drama)
# label  : human-readable emotion name shown in the UI
EMOTION_VOICE_MAP = {
    "joy": {
        "pitch":  10.0,
        "rate":   8.0,
        "volume": "medium",
        "pause":  0,
        "label":  "Joy / Positive",
        "emoji":  "😊",
        "color":  "#f9c74f",
    },
    "neutral": {
        "pitch":  0.0,
        "rate":   0.0,
        "volume": "medium",
        "pause":  0,
        "label":  "Neutral",
        "emoji":  "😐",
        "color":  "#90e0ef",
    },
    "frustrated": {
        "pitch":  12.0,
        "rate":   8.0,
        "volume": "loud",
        "pause":  200,
        "label":  "Frustrated / Negative",
        "emoji":  "😤",
        "color":  "#ef233c",
    },
    "surprised": {
        "pitch":  15.0,
        "rate":   10.0,
        "volume": "loud",
        "pause":  0,
        "label":  "Surprised",
        "emoji":  "😲",
        "color":  "#f77f00",
    },
    "concerned": {
        "pitch":  -8.0,
        "rate":   -10.0,
        "volume": "soft",
        "pause":  250,
        "label":  "Concerned",
        "emoji":  "😟",
        "color":  "#6a4c93",
    },
    "inquisitive": {
        "pitch":  6.0,
        "rate":   3.0,
        "volume": "medium",
        "pause":  0,
        "label":  "Inquisitive",
        "emoji":  "🤔",
        "color":  "#43aa8b",
    },
}

# ── Audio file paths ──────────────────────────────────────────────
AUDIO_BEFORE_FILENAME = "audio/audio-before.mp3"
AUDIO_AFTER_FILENAME  = "audio/audio-after.mp3"

# ── gTTS settings ─────────────────────────────────────────────────
GTTS_LANG = "en"
GTTS_TLD  = "com"

# ── Flask settings ────────────────────────────────────────────────
DEBUG = True
HOST  = "127.0.0.1"
PORT  = 5000