<<<<<<< HEAD
# Voice Assistant Project

This project is a Python voice assistant for G H Raisoni University Saikheda. It supports:

- voice input with `SpeechRecognition`
- spoken responses with automatic text display at the same time
- automatic keyboard fallback when microphone access is unavailable
- local offline speech with Piper voice models for faster replies
- fallback online speech with `edge-tts` when local Windows voices are missing
- English and Hindi language selection
- answers for courses, fees, admission, facilities, exams, contact details, timings, and current date or time
- a Python website with browser voice input and voice-first response timing

## Project Structure

- `voice assistant 1.py` compatibility launcher
- `voice_assistant/assistant.py` assistant logic
- `voice_assistant/data.py` structured college data and localized messages
- `voice_assistant/main.py` CLI entry point
- `voice_assistant/webapp.py` Flask web backend
- `voice_assistant/templates/index.html` website UI
- `voice_assistant/static/app.js` browser voice and chat flow
- `voice_assistant/static/styles.css` website styling
- `run_web.py` web launcher
- `voice_assistant/__main__.py` package runner
- `pyproject.toml` package metadata
- `requirements.txt` Python dependencies

## Setup

1. Create a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

If `PyAudio` fails to install on your system, you can still run the project in keyboard mode.

## Run

Default GHRU voice mode:

```powershell
python "voice assistant 1.py"
```

Package mode:

```powershell
python -m voice_assistant
```

Website mode:

```powershell
python run_web.py
```

Then open [http://127.0.0.1:5000](http://127.0.0.1:5000).

Keyboard-only mode:

```powershell
python "voice assistant 1.py" --no-voice-input
```

Set a default language:

```powershell
python "voice assistant 1.py" --language en
python "voice assistant 1.py" --language hi
```

## Example Questions

- `tell me about the college`
- `what courses are available`
- `tell me the fees`
- `how does admission work`
- `what facilities are available`
- `what is the exam schedule`
- `give me department contact details`
- `what are the office timings`
- `what is the time`
- `exit`

## Notes

- Google speech recognition needs internet access when voice input is enabled.
- Piper offline speech is used first for spoken responses, then `edge-tts`, then local Windows speech fallbacks if needed.
- If microphone input fails at runtime, the assistant automatically falls back to text input while continuing to respond by voice.
- Assistant replies are also shown in writing so you can read the same response that is being spoken.
- In the website, the browser handles microphone capture and speech playback, while the Python backend keeps the assistant logic and response order.
- The website preserves the voice process: assistant voice starts first, text appears one second later, and the next listening cycle starts only after the response completes.
=======
# ghru-voice-assistant
Bilingual AI Voice Assistant for G H Raisoni University

An intelligent bilingual (English & Hindi) AI-powered college inquiry assistant developed for **G H Raisoni University Saikheda**.  
The system acts as a virtual guide for students, parents, and visitors by providing instant information about admissions, courses, fees, departments, facilities, contact details, and more through voice and text interaction.

---

## 🚀 Features

- 🌐 Bilingual Support (English + Hindi)
- 🎤 Speech-to-Text (Voice Input)
- 🔊 Text-to-Speech (AI Voice Response)
- 💬 Text Chat Support
- ⚡ Fast Query Response
- 🎓 College Information Assistant
- 📱 Responsive Web Interface
- 🧠 Intent-Based Smart Responses
- 🔄 Real-Time Interaction
- 📴 Offline Voice Fallback Support

---

## 🛠️ Technologies Used

### Frontend
- HTML5
- CSS3
- JavaScript
- Bootstrap

### Backend
- Python
- Flask

### Voice & AI Technologies
- SpeechRecognition
- Google Web Speech API
- Edge-TTS
- pyttsx3
- NLP-based Intent Matching

---

## 📂 Project Structure

```bash
ghru-voice-assistant/
│
├── app.py
├── assistant.py
├── data.py
├── requirements.txt
├── README.md
│
├── static/
│   ├── css/
│   ├── js/
│   └── audio/
│
├── templates/
│   └── index.html
│
└── assets/
>>>>>>> 035ef05b02cef148256ced34670f1b27cb13f74f
