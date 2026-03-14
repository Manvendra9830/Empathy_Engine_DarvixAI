# 🎙 Empathy Engine — Emotion-Aware Text-to-Speech System

> *An AI engineering challenge submission that gives synthesised speech a human voice.*

---

## 📋 Project Description

**Empathy Engine** is a Flask-based web application that converts plain text into
emotionally expressive audio.  Rather than generating flat, robotic speech, it:

1. **Detects the emotion** in the input text using a pre-trained HuggingFace
   DistilRoBERTa model fine-tuned on emotion data.
2. **Maps the emotion** to a set of vocal parameters (pitch, rate, volume, pauses).
3. **Generates SSML** (Speech Synthesis Markup Language) markup that encodes those
   parameters.
4. **Produces two audio files** — a plain "before" recording and an emotion-modulated
   "after" recording — so you can hear the difference side by side.

---

## 🏗️ System Architecture

```
User Input Text
       │
       ▼
┌─────────────────┐
│  Flask (app.py) │  ← POST /generate
└────────┬────────┘
         │
   ┌─────┴──────┐
   ▼            ▼
gTTS         emotion_detector.py
(audio-      ├── HuggingFace pipeline
 before)     └── j-hartmann/emotion-english-distilroberta-base
                       │
                       ▼
               voice_mapper.py
               └── emotion → {pitch, rate, volume, pause}
                       │
                       ▼
               ssml_generator.py
               └── build <speak><prosody .../></speak>
                       │
                       ▼
               tts_engine.py
               ├── gTTS  → raw audio
               └── pydub → pitch shift + tempo + volume
                       │
                       ▼
               audio-after.mp3
```

Both audio files are served back to the browser and played in the UI for
instant A/B comparison.

---

## 🧠 Emotion → Voice Mapping Logic

The mapping is defined in `config.py` and applied by `voice_mapper.py`.

| Emotion       | Pitch   | Rate   | Volume | Pause  | Rationale |
|---------------|---------|--------|--------|--------|-----------|
| 😊 Joy        | +20%    | fast   | medium | none   | Enthusiasm = higher pitch, quicker cadence |
| 😐 Neutral    | default | medium | medium | none   | Baseline — no modulation |
| 😤 Frustrated | -15%    | slow   | loud   | 300 ms | Heaviness + deliberate pacing + volume to signal tension |
| 😲 Surprised  | +30%    | fast   | loud   | none   | Maximum pitch spike + urgency |
| 😟 Concerned  | -10%    | slow   | soft   | 200 ms | Gravity + gentle delivery |
| 🤔 Inquisitive| +10%    | medium | medium | none   | Slight upturn signals a question |

**Intensity scaling:** if the model's confidence score falls below 0.55 the pitch
modulation is scaled down proportionally so that borderline detections don't
produce jarring speech.

**Inquisitive heuristic:** if the input contains a `?` character and the base
detection is `neutral` or `joy`, the label is overridden to `inquisitive`.

---

## 📐 Why SSML?

SSML (Speech Synthesis Markup Language) is the W3C standard for controlling TTS
engines.  Using it as an intermediate representation:

* Makes the vocal parameters **explicit and inspectable** — the generated SSML is
  shown in the UI.
* Keeps the codebase **engine-agnostic**: swapping gTTS for Google Cloud TTS or
  ElevenLabs requires only changes in `tts_engine.py`, not in the mapping logic.
* Enables future features (emphasis, phoneme overrides, say-as) with zero changes
  to upstream modules.

Because gTTS does not accept SSML directly, the parameters are extracted and
applied as audio-domain post-processing using **pydub + ffmpeg**.

---

## 📁 Project Structure

```
empathy-engine/
├── app.py                 # Flask server & route handlers
├── emotion_detector.py    # HuggingFace emotion classification
├── voice_mapper.py        # Emotion → vocal parameter lookup
├── ssml_generator.py      # SSML markup builder
├── tts_engine.py          # Audio generation & pydub modulation
├── config.py              # All constants & mapping tables
├── utils.py               # Shared helpers (logging, sanitisation, …)
├── requirements.txt
├── README.md
├── templates/
│   └── index.html         # Single-page UI
└── static/
    ├── css/
    │   └── style.css
    └── audio/             # Generated audio files (git-ignored)
        ├── audio-before.mp3
        └── audio-after.mp3
```

---

## ⚙️ Installation & Setup

### Prerequisites

| Tool    | Version  | Install |
|---------|----------|---------|
| Python  | ≥ 3.9    | [python.org](https://python.org) |
| ffmpeg  | any      | see below |
| pip     | ≥ 23     | bundled with Python |

**Installing ffmpeg:**

```bash
# Ubuntu / Debian
sudo apt-get update && sudo apt-get install -y ffmpeg

# macOS (Homebrew)
brew install ffmpeg

# Windows (Chocolatey)
choco install ffmpeg
```

### Step-by-step

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/empathy-engine.git
cd empathy-engine

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Run the application
python app.py
```

### 5. Open in your browser

```
http://127.0.0.1:5000
```

> **First run note:** on startup the app downloads the HuggingFace emotion model
> (~260 MB).  Subsequent runs load it from the local cache instantly.

---

## 🚀 Example Usage

1. Open `http://127.0.0.1:5000`.
2. Type or paste any sentence, for example:
   > *"I can't believe we pulled it off — this is absolutely incredible!"*
3. Click **Generate Speech** (or press `Ctrl+Enter`).
4. The system will:
   - Show the detected emotion (`Joy / Positive — 94% confidence`).
   - Display the vocal parameters applied (`pitch +20% · rate fast · volume medium`).
   - Show the generated SSML markup.
   - Play both the **Before** (flat) and **After** (emotion-aware) audio clips.

You can also click any of the **sample sentences** in the sidebar to auto-fill
the input box.

---

## 🔌 API Reference

### `POST /generate`

**Request body (JSON)**
```json
{ "text": "This is absolutely incredible!" }
```

**Response body (JSON)**
```json
{
  "emotion":      "joy",
  "label":        "Joy / Positive",
  "emoji":        "😊",
  "color":        "#f9c74f",
  "confidence":   "94%",
  "pitch":        "+20%",
  "rate":         "fast",
  "volume":       "medium",
  "ssml":         "<speak>\n  <prosody pitch=\"+20%\" rate=\"fast\">\n    This is absolutely incredible!\n  </prosody>\n</speak>",
  "all_scores":   [{"label": "Joy", "score_pct": "94.1"}, ...],
  "audio_before": "/static/audio/audio-before.mp3?t=1718000000",
  "audio_after":  "/static/audio/audio-after.mp3?t=1718000000",
  "error":        null
}
```

### `GET /health`
Returns `{"status": "ok", "service": "empathy-engine"}`.

---

## 🛠️ Design Choices

### Emotion model
`j-hartmann/emotion-english-distilroberta-base` was chosen because it:
- Covers 7 emotion classes out-of-the-box (anger, disgust, fear, joy, neutral,
  sadness, surprise).
- Is compact enough (~260 MB) to run comfortably on CPU.
- Outperforms simpler lexicon-based approaches (VADER, TextBlob) on short
  conversational sentences.

### Audio modulation via pydub
Google Cloud TTS natively supports SSML but requires billing credentials.
`gTTS` is free and works offline but does not support SSML.  We therefore use
pydub to apply the prosody parameters as **audio-domain post-processing**:
- Pitch shift via frame-rate manipulation + resampling.
- Tempo change via the same mechanism (changes speed without artefacts for speech).
- Volume change via dB gain.

This approach keeps the project fully runnable with no API keys while still
producing an audible before/after difference.

---

## 🔮 Future Improvements

- **Google Cloud TTS / ElevenLabs backend** — native SSML support for higher
  fidelity modulation.
- **Real-time streaming** — stream audio chunks as they are generated instead of
  waiting for the full file.
- **Multi-sentence analysis** — detect emotion independently per sentence and
  stitch modulated clips together.
- **User-adjustable intensity slider** — let the user dial the strength of
  modulation from subtle to dramatic.
- **Voice selection** — choose from multiple speaker voices (male, female, accents).
- **Export / share** — download the modulated audio directly from the UI.

---

## 📄 License

MIT — see `LICENSE` for details.
