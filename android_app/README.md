# CCAF Adaptive Filter Android & Web Simulator Application

Mobile implementation and interactive simulator for **Conformal-Controlled Adaptive Filtering (CCAF)** supporting distribution-free uncertainty quantification, acoustic echo cancellation, and real-time noise reduction.

---

## 🚀 What's New: Major Interactive & Format Enhancements

### 1. Instant Zero-Latency A/B Shifting
- **Seamless Live Shifting:** Users can now switch between **Original Audio** and **Model Output** instantaneously with zero playback interruption, zero restart, and zero clicking/popping artifacts (via smooth 15 ms cross-fade interpolation).
- **Interactive Switcher Bar:** Two high-contrast toggle chips (`🔈 Original File` and `🎧 Model Output`) allow real-time human hearing verification of filter performance while listening.

### 2. Universal Multi-Format Audio Support
- **Full Ingestion Support:** The app now decodes and filters **WAV, MP3, AAC, FLAC, M4A, OGG/Opus, and WEBM**.
- **Multi-Format Export:** Processed/cleaned audio can be downloaded or saved to memory in **16-bit Lossless PCM WAV** or **Compressed MP3 (128 kbps)**.

### 3. Presets & Interactive Waveform
- **Quick Preset Feeds:** Instantly test without needing to supply custom files:
  - `Speech + Room Echo (AEC)`: Microsoft AEC real challenge recording.
  - `Synthetic Tone + Noise`: Dynamic sinusoidal speech with Gaussian noise.
  - `Impulsive Outlier Burst`: Evaluates CCAF's resilience against non-Gaussian noise spikes.
- **Dual-Trace Synchronous Plot:** Electric Cyan (Original) vs. Vibrant Amber (After Model) with dynamic zoom and scrubber.

---

## 📱 Three Core Operational Modes

### 1. Live Record (Microphone Stream)
- Captures microphone audio in real-time (16 kHz Linear PCM).
- Filters audio live through the active adaptive filter.
- Instant A/B playback switcher to compare unprocessed room audio with adaptive filter output.
- Save to storage as WAV or MP3.

### 2. Select File (Storage Audio Processor)
- Select any audio track from device memory (`.wav`, `.mp3`, `.m4a`, `.aac`, `.flac`, `.ogg`).
- Instantaneous processing with real-time conformal metrics (empirical coverage and Winkler sharpness score).
- Live A/B shifting during continuous playback.
- Export filtered output to memory.

### 3. Choose Model (7 Research Algorithms + Custom)
- **Proposed CCAF-DB:** Conformal-Controlled Adaptive Filter with Dead-Band step-size control.
- **Decoupled ACI:** Fixed NLMS with open-loop Adaptive Conformal Inference.
- **NLMS (fast):** $\mu = 0.50$ for rapid convergence.
- **NLMS (slow):** $\mu = 0.05$ for low steady-state floor.
- **Kwong VSS-LMS:** Error-power driven step-size adjustment.
- **Benesty NP-VSS:** Nonparametric noise-floor estimating filter.
- **Convex Combination:** Sigmoidal mixing of fast and slow filters.
- **Add New Model:** Custom parameter builder & JSON configuration importer.

---

## 🌐 Quick Test via Web Simulator

To run the interactive simulator in any web browser:
```bash
python -m http.server 8080 -d android_app/web_simulator
```
Then open `http://localhost:8080` in Chrome, Firefox, Safari, or Edge.
