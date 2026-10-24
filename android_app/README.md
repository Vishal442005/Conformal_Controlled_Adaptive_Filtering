# CCAF Adaptive Filter Android App & Pro Web Simulator (v1.1.0)

Mobile implementation and interactive simulator for **Conformal-Controlled Adaptive Filtering (CCAF)** supporting distribution-free uncertainty quantification, acoustic echo cancellation, and real-time noise reduction.

---

## 📦 Download Ready-to-Install APK
* **Updated Signed APK (v1.1.0):** [**`android_app/CCAF_Adaptive_Filter_v1.1.0.apk`**](file:///i:/Research2/android_app/CCAF_Adaptive_Filter_v1.1.0.apk)
* **Direct Install via ADB:**
  ```bash
  adb install -r android_app/CCAF_Adaptive_Filter_v1.1.0.apk
  ```

---

## 🚀 What's New in v1.1.0: Major Interactive & Architectural Upgrades

### 1. Universal Multi-Format Audio Ingestion
- **Full Format Support:** Ingests and decodes **MP3, WAV, FLAC, M4A, AAC, OGG/Opus, and WEBM** natively on Android and in the browser.
- **Drag-and-Drop Zone:** Drag audio files directly into the simulator with automatic format detection and duration inspection.
- **Multi-Format Export:** Export processed audio in **16-bit Lossless PCM WAV** or **Compressed MP3 (128 kbps)** via embedded client-side LAME encoder.

### 2. Multi-Mode Advanced Visualizer Engine
Switch dynamically between three rendering views:
- **Dual Oscilloscope (Wave):** Synchronous dual-trace time-domain comparison (Electric Cyan for original vs. Neon Amber for filtered output) with interactive playhead tracking.
- **64-Band Real-Time FFT Spectrum (FFT):** Dual-color frequency distribution bars (20 Hz to 8 kHz) showing attenuation of echo and noise across bands.
- **90% Conformal Uncertainty Ribbon (Ribbon):** Plots the dynamic confidence intervals $[y_t \pm q_t s_t]$ as a translucent emerald band, with red outlier dots marking nonconformity breaches.

### 3. Comprehensive 8-Parameter Live Telemetry Grid
1. **Instantaneous Step Size ($\mu_t$):** Dynamic adaptation rate.
2. **Empirical Coverage ($1 - \hat{\alpha}_t$):** Rolling percentage compared to the 90.0% nominal target.
3. **Winkler Interval Loss:** Penalty scoring interval width and coverage breaches.
4. **ERLE Attenuation (dB):** Instantaneous Echo Return Loss Enhancement ($10 \log_{10} \frac{P_{\text{orig}}}{P_{\text{filt}}}$).
5. **Nonconformity Metric ($|e_t| / \sigma_t$):** Real-time distribution shift and outlier surge monitor.
6. **Dead-Band Status ($\tau = 0.04$):** Visual `ACTIVE` / `SLEEP` indicator verifying zero steady-state misadjustment.
7. **ACI Quantile State ($\hat{\alpha}_t$):** Continuous quantile calibration tracker.
8. **FLOP Complexity / Sample:** $2M + 5 = 133$ FLOPs vs. $O(M^2) = 8,192$ FLOPs.

### 4. Continuous Cross-Fader & Transport Scrubber
- **Smooth Cross-Fader Slider:** Blend continuously from 100% Original $\leftrightarrow$ 100% Filtered audio using an equal-power crossfade curve without restarting playback.
- **Instant Snap Chips:** `🔈 100% Real`, `🎚️ 50/50 Mix`, `🎧 100% Filtered`.
- **Interactive Scrubber:** Click-to-seek waveform progress bar with elapsed and total duration timestamps (`0:04 / 0:15`).
- **Loop Mode:** Seamless loop toggle (`🔁 Loop: ON / OFF`) for continuous acoustic testing.
- **Live Hyperparameter Tuner:** Real-time sliders for $\mu_{\max}$, $\mu_{\min}$, $\alpha$, $\tau$, and $\gamma$.

---

## 📱 Three Core Operational Modes

### 1. Live Record (Microphone Stream)
- Captures microphone audio in real time (16 kHz Linear PCM).
- Filters audio live through the active adaptive filter.
- Seamless post-recording A/B shifting between raw microphone audio and filter output.
- Export to storage as WAV or MP3.

### 2. Select File (Storage Audio Processor)
- Select any audio track from device storage (`.mp3`, `.wav`, `.m4a`, `.aac`, `.flac`, `.ogg`).
- Real-time batch filtering with live dual-line waveform visualization.
- Instant A/B cross-fading during continuous playback.
- Export processed audio directly to memory.

### 3. Choose Model (7 Research Algorithms + Custom)
- **Proposed CCAF-DB:** Conformal-Controlled Adaptive Filter with Dead-Band step-size control.
- **Decoupled ACI:** Fixed NLMS with open-loop Adaptive Conformal Inference.
- **NLMS (fast):** $\mu = 0.50$ for rapid initial convergence.
- **NLMS (slow):** $\mu = 0.05$ for low steady-state misadjustment.
- **Kwong VSS-LMS:** Error-power driven step-size adjustment.
- **Benesty NP-VSS:** Nonparametric noise-floor estimating filter.
- **Convex Combination:** Sigmoidal mixing of fast and slow filters.
- **Add New Model:** Custom parameter builder & JSON configuration importer.

---

## 🌐 Run Standalone Web Simulator

To run the interactive simulator in any modern browser (Chrome, Edge, Firefox, Safari):
```bash
python -m http.server 8080 -d android_app/web_simulator
```
Then navigate to `http://localhost:8080`.
