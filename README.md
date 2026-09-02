# 🎬 AI-Powered Dubbing & Language Learning Platform

An interactive, modular web application that turns any video into a personalized language learning experience. By combining speech-to-text, local LLMs, and media processing, this platform allows users to extract scripts, test their vocabulary, and actively dub characters in real-time.

## ✨ Key Features

* **Intelligent Hub & Script Extraction:** Upload any `.mp4` video. The app uses OpenAI's Whisper to automatically generate a timed script and hardcode subtitles onto the video.
* **AI Pre-Dubbing Quizzes:** Generates contextual exercises based on the video's script. Choose between a fast, logic-based algorithm (Base) or advanced LLM-generated quizzes (Plus) for translations, synonyms, and fill-in-the-blanks.
* **Active Dubbing Studio:** Select which lines to dub. The app mutes the original video during your lines, records your voice, and seamlessly mixes it back into the scene.
* **Auto-Multilingual Dubbing:** Uses AI text-to-speech (gTTS) and FFmpeg to instantly translate the original script and generate a fully dubbed video in a new language.
* **Performance Evaluation:** Transcribes your recorded audio and uses a local LLM to compare it against the original script-

## 🛠️ Tech Stack

* **Frontend & UI:** [NiceGUI](https://nicegui.io/) (Python-based reactive web framework)
* **Speech-to-Text:** [OpenAI Whisper](https://github.com/openai/whisper)
* **Large Language Model:** [Ollama](https://ollama.ai/) (Local LLM inference, e.g., Gemma)
* **Text-to-Speech:** gTTS (Google Text-to-Speech)
* **Media Processing:** FFmpeg & `ffmpeg-python`
* **Audio Recording:** `sounddevice` & `soundfile`

## ⚙️ Prerequisites

Before running the application, ensure you have the following installed on your system:

1. **Python 3.8+**
2. **FFmpeg:** Must be installed and added to your system's PATH. 
3. **Ollama:** Installed and running locally. Make sure you have pulled the required model (e.g., `ollama run gemma`).
