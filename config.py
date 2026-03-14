"""
config.py - Central configuration for the Empathy Engine
All constants, model names, and emotion-to-voice mappings live here.
"""

# ── HuggingFace model ──────────────────────────────────────────────────────────
# j-hartmann/emotion-english-distilroberta-base outputs 7 labels:
#   anger, disgust, fear, joy, neutral, sadness, surprise
EMOTION_MODEL_NAME = "j-hartmann/emotion-english-distilroberta-base"

# ── Emotion label normalisation ────────────────────────────────────────────────
# Maps raw model labels → canonical app labels
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
# pitch  : SSML prosody value  e.g. "+20%", "-15%", "default"
# rate   : SSML prosody value  e.g. "fast", "slow", "medium"
# volume : SSML prosody value  e.g. "loud", "soft", "medium"
# pause  : milliseconds inserted after the first sentence (adds drama)
# label  : human-readable emotion name shown in the UI
EMOTION_VOICE_MAP = {
    "joy": {
        "pitch":  "+20%",
        "rate":   "fast",
        "volume": "medium",
        "pause":  0,
        "label":  "Joy / Positive",
        "emoji":  "😊",
        "color":  "#f9c74f",
    },
    "neutral": {
        "pitch":  "default",
        "rate":   "medium",
        "volume": "medium",
        "pause":  0,
        "label":  "Neutral",
        "emoji":  "😐",
        "color":  "#90e0ef",
    },
    "frustrated": {
        "pitch":  "-15%",
        "rate":   "slow",
        "volume": "loud",
        "pause":  300,
        "label":  "Frustrated / Negative",
        "emoji":  "😤",
        "color":  "#ef233c",
    },
    "surprised": {
        "pitch":  "+30%",
        "rate":   "fast",
        "volume": "loud",
        "pause":  0,
        "label":  "Surprised",
        "emoji":  "😲",
        "color":  "#f77f00",
    },
    "concerned": {
        "pitch":  "-10%",
        "rate":   "slow",
        "volume": "soft",
        "pause":  200,
        "label":  "Concerned",
        "emoji":  "😟",
        "color":  "#6a4c93",
    },
    "inquisitive": {
        "pitch":  "+10%",
        "rate":   "medium",
        "volume": "medium",
        "pause":  0,
        "label":  "Inquisitive",
        "emoji":  "🤔",
        "color":  "#43aa8b",
    },
}

# ── Audio file paths (relative to static/) ────────────────────────────────────
AUDIO_BEFORE_FILENAME = "audio/audio-before.mp3"
AUDIO_AFTER_FILENAME  = "audio/audio-after.mp3"

# ── gTTS settings ─────────────────────────────────────────────────────────────
GTTS_LANG = "en"
GTTS_TLD  = "com"   # accent: com=US, co.uk=British, com.au=Australian

# ── Flask settings ────────────────────────────────────────────────────────────
DEBUG = True
HOST  = "127.0.0.1"
PORT  = 5000
