# 🎙 Empathy Engine — Emotion-Aware Text-to-Speech System

An AI engineering challenge submission that gives synthesised speech a human voice.

## 📋 Project Description

**Empathy Engine** is a Flask-based web application that converts plain text into emotionally expressive audio.

Rather than generating flat, robotic speech, it:

*   **Detects the emotion** in the input text using a pre-trained HuggingFace DistilRoBERTa model fine-tuned on emotion data.
*   **Maps the emotion** to a set of vocal parameters (pitch, rate, volume, pauses).
*   **Generates SSML** (Speech Synthesis Markup Language) markup that encodes those parameters.
*   **Produces two audio files** — a plain "before" recording and an emotion-modulated "after" recording — so you can hear the difference side by side.

---

## 🏗 System Architecture

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

Both audio files are served back to the browser and played in the UI for instant A/B comparison.

---

## 🧠 Emotion → Voice Mapping Logic

The mapping is defined in `config.py` and applied by `voice_mapper.py`.

Earlier versions used fixed pitch and rate values, which produced exaggerated emotional speech. The system now uses research-informed base values combined with confidence-scaled modulation to produce more natural emotional speech.

### **Base Prosody Mapping**

| Emotion | Base Pitch | Base Rate | Volume | Pause | Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 😊 Joy | +10% | +8% | medium | none | Enthusiasm expressed through slightly higher pitch and faster cadence |
| 😐 Neutral | 0% | 0% | medium | none | Baseline speech |
| 😤 Frustrated | +12% | +8% | loud | 200 ms | Increased intensity and urgency |
| 😲 Surprised | +15% | +10% | loud | none | Sudden excitement produces highest pitch |
| 😟 Concerned | −8% | −10% | soft | 250 ms | Lower energy and slower delivery |
| 🤔 Inquisitive | +6% | +3% | medium | none | Slight pitch rise suggests questioning |

*These values represent base emotional prosody ranges before confidence scaling is applied.*

---

## 📊 Research Basis for Emotional Prosody

The prosody ranges used in Empathy Engine are informed by research in emotional speech and acoustic phonetics. Human emotions in speech are primarily conveyed through variations in:

| Acoustic Feature | Role in Emotional Speech |
| :--- | :--- |
| **Pitch (Fundamental Frequency)** | Indicates emotional arousal |
| **Speech Rate** | Reflects urgency or calmness |
| **Intensity (Volume)** | Signals emotional strength |
| **Pauses** | Adds emphasis or hesitation |

Research shows that natural emotional speech usually varies pitch and tempo within approximately **5–15%** relative to neutral speech. Using values outside this range often produces unnatural or exaggerated speech, especially in synthetic voice systems.

The base values used in `config.py` were derived from the following research:

| Paper | Contribution |
| :--- | :--- |
| **Scherer (2003)** – Vocal Communication of Emotion | Explains how pitch, intensity, and tempo encode emotions |
| **Dhamyal et al. (2019)** – The Phonetic Bases of Vocal Expressed Emotion | Provides phonetic analysis of emotional speech |
| **Banse & Scherer (1996)** – Acoustic Profiles in Vocal Emotion Expression | Large-scale acoustic analysis of emotional vocal signals |

### **Research links:**
*   [Scherer (2003)](https://www.sci.brooklyn.cuny.edu/~levitan/nlp-psych/papers/Scherer03.pdf)
*   [Dhamyal et al. (2019)](https://arxiv.org/pdf/1911.05733)
*   [Banse & Scherer (1996)](https://pubmed.ncbi.nlm.nih.gov/8851745/)

---

## 🎚 Confidence-Scaled Prosody Modulation

Instead of applying fixed pitch and rate values, the Empathy Engine dynamically scales emotional intensity based on the confidence score produced by the emotion classifier. This prevents exaggerated speech when the model is uncertain.

### **Modulation Formula**
`final_pitch = base_pitch × confidence`  
`final_rate  = base_rate × confidence`

| Variable | Description |
| :--- | :--- |
| **base_pitch** | Pitch value from `config.py` |
| **base_rate** | Rate value from `config.py` |
| **confidence** | Probability score from the emotion classifier |

### **Example**
**Detected emotion:** Joy  
**Confidence:** 0.72  
**Base parameters:** pitch = +10%, rate = +8%  
**Final applied values:** pitch = +7.2%, rate = +5.76%

### **Benefits of Confidence Scaling**
| Benefit | Explanation |
| :--- | :--- |
| **Natural speech** | Prevents exaggerated pitch shifts |
| **Robust behavior** | Low confidence → subtle changes |
| **Expressiveness** | High confidence → stronger emotion |
| **Smooth audio output** | Avoids robotic speech |

---

## 📐 Why SSML?

SSML (Speech Synthesis Markup Language) is the W3C standard for controlling TTS engines. Using it as an intermediate representation:
*   Makes vocal parameters **explicit and inspectable**
*   Keeps the system **engine-agnostic**
*   Allows easy integration with Google Cloud TTS or ElevenLabs

Because gTTS does not support SSML directly, Empathy Engine applies prosody changes using **pydub + ffmpeg** as post-processing.

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

## ⚙ Installation & Setup

### **Prerequisites**
| Tool | Version |
| :--- | :--- |
| **Python** | ≥ 3.9 |
| **ffmpeg** | any |
| **pip** | ≥ 23 |

### **Install ffmpeg:**
*   **Ubuntu:** `sudo apt-get install ffmpeg`
*   **Mac:** `brew install ffmpeg`
*   **Windows:** `choco install ffmpeg`

### **Setup**
```bash
git clone https://github.com/Manvendra9830/Empathy_Engine_DarvixAI.git
cd empathy-engine

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt

python app.py
```

Open: `http://127.0.0.1:5000`

---

## 🚀 Example Usage

1. Enter text in the UI
2. Click **Generate Speech**
3. The system executes the following:

| Step | Result |
| :--- | :--- |
| **1. Emotion detection** | Joy / Positive (94%) |
| **2. Prosody mapping** | pitch +7% · rate +6% |
| **3. SSML generation** | `<prosody pitch="+7%">` |
| **4. Audio output** | before vs emotion-aware speech |

---

## 🔌 API Reference

### `POST /generate`
**Request**
```json
{ "text": "This is absolutely incredible!" }
```
**Response**
```json
{
 "emotion": "joy",
 "confidence": "94%",
 "pitch": "+7.2%",
 "rate": "+5.7%",
 "audio_before": "...",
 "audio_after": "..."
}
```

---

## 🛠 Design Choices

| Component | Reason |
| :--- | :--- |
| **HuggingFace emotion model** | Accurate and compact emotion detection |
| **gTTS** | Free and reliable speech synthesis |
| **pydub + ffmpeg** | Flexible audio-domain prosody manipulation |
| **SSML representation** | Standardized and engine-agnostic design |

---

## 🔮 Future Improvements

*   **Native SSML support** via Google Cloud TTS or ElevenLabs
*   **Real-time speech streaming** for lower latency
*   **Sentence-level emotion detection** for long-form text
*   **User-adjustable intensity slider** to manually override scaling
*   **Multiple voice options** (male, female, accents)
*   **Export / share** generated emotional speech

---

## 📄 License

MIT License — see `LICENSE` for details.
