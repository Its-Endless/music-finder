# 🎵 Local Audio Fingerprinting & Music Recognition

A complete Shazam-style audio recognition system built from scratch using Python.

This project listens to audio, generates spectral fingerprints, stores them in a
database, and identifies songs by matching hashes — just like real audio
fingerprinting systems (Shazam, Echoprint, etc.).

It includes:

✅ Real-time microphone recording  
✅ Local-peak constellation fingerprinting  
✅ Hash generation for fast lookup  
✅ SQLite fingerprint database  
✅ Matching engine with offset alignment  
✅ Web API (Flask)  
✅ Web UI with browser microphone access  
✅ Batch song ingestion (multi-song fingerprinting)  
✅ Debug tools (spectrogram + peaks, match diagnostics)

---

# 🚀 Features

### 🎤 Record audio & generate fingerprints
Record a snippet and extract spectral peaks (constellation map) using STFT.

### 🧠 Fast Hash-based Matching (Shazam-like)
Matches fingerprints using hash collisions + time-offset alignment.

### 🗄 SQLite Database for Fingerprints
Stores:
- song metadata  
- fingerprint hashes  
- time offsets  

### 🌐 Flask API
Send any audio file (`wav/mp3/m4a/ogg/webm`) to:
```

POST /match

```
and receive JSON match results.

### 🌍 Web UI (HTML + JS)
- Record via browser microphone  
- Auto-send audio to API  
- Display matching results  

---

# 📸 Demo Screenshot (optional)
*(Insert your spectrogram or UI screenshot here)*

---

# 🏗 Project Structure

```

Shazam Clone/
├── src/
│   ├── api.py
│   ├── capture.py
│   ├── fingerprint.py
│   ├── matcher.py
│   ├── db.py
│   ├── debug_peaks.py
│   ├── debug_matching.py
│   └── **init**.py
│
├── static/
│   └── index.html           # Web UI
│
├── tests/
│   └── test_basic.py
│
├── fingerprints.db          # (ignored after cleanup)
├── recording.wav            # (ignored)
├── query.wav                # (ignored)
└── README.md

````

---

# 🔧 Installation

### 1. Clone repository
```bash
git clone https://github.com/<your-username>/Shazam-Clone.git
cd Shazam-Clone
````

### 2. Create & activate environment

```bash
conda create -n shazam python=3.10 -y
conda activate shazam
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

(If you don't have a requirements file, install manually:)

```bash
pip install librosa soundfile pydub sounddevice flask sqlalchemy pytest audioread
```

### 4. Install FFmpeg

Required for `.webm → .wav` conversion.

Download from:
[https://www.gyan.dev/ffmpeg/builds/](https://www.gyan.dev/ffmpeg/builds/)

Add to PATH:

```
C:\ffmpeg\bin
```

Check:

```bash
ffmpeg -version
```

---

# 🎙 Record Audio (Testing)

Record 5 seconds:

```bash
python src/capture.py
```

---

# 🧬 Fingerprint Audio

Store fingerprints in the DB:

```bash
python -m src.fingerprint recording.wav "test_recording"
```

Debug peaks:

```bash
python -m src.debug_peaks recording.wav
```

---

# 🔍 Match Audio

Match any audio file against the database:

```bash
python -m src.matcher query.wav
```

Expected output:

```
Top 1 candidates:
1. song_id=1 score=713 best_delta=5 name='test_recording' path='recording.wav'
```

---

# 🌐 Run the API

```bash
python -m src.api
```

API will run at:

```
http://127.0.0.1:5000
```

### Test with curl:

```bash
curl -X POST -F "file=@recording.wav" http://127.0.0.1:5000/match
```

---

# 🖥 Web UI

Open:

```
static/index.html
```

Click **🎤 Record & Identify**
Browser → records audio → sends to API → shows match.

Supports `.webm` audio from browsers using ffmpeg+pydub conversion.

---

# 📚 Add Multiple Songs (Batch Fingerprinting)

Create a folder:

```
songs/
   song1.mp3
   song2.wav
   song3.m4a
   ...
```

Batch script (coming soon):

```bash
python -m src.batch_fingerprint songs/
```

---

# 🧪 Tests

Run tests:

```bash
pytest
```

---

# 🧠 How It Works (Brief Architecture)

### 1. STFT Spectrogram

Convert audio → time-frequency domain.

### 2. Peak Picking (Constellation Map)

Find local maxima → frequency-time anchor points.

### 3. Hashing

Pair peaks using:

```
(hash = sha1(freq1, freq2, dt))
```

### 4. Store in DB

Each hash → (song_id, time_offset).

### 5. Matching

Query audio → generate hashes → lookup collisions → align using time-deltas → score.

Very close to the real Shazam patent methodology.

---

# 📌 Future Improvements

* Batch song ingestion
* Confidence scoring
* Noise robustness
* Spectrogram UI
* Real-time continuous listening
* Mobile app integration
* Deploy the API to cloud

---

# 🤝 Contributing

PRs welcome!
Open an issue for feature requests or ideas.

---

# 📄 License

MIT License.

---
