# Conformal-Controlled Adaptive Filtering (CCAF)

Official implementation, experimental benchmarks, and reproduction suite for:  
**"Conformal-Controlled Adaptive Filtering: Distribution-Free Uncertainty Bounds and Coverage-Driven Step-Size Control"**

[![Release](https://img.shields.io/badge/release-v1.2.0-blue.svg)](https://github.com/Vishal442005/Conformal_Controlled_Adaptive_Filtering/releases)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23609984.svg)](https://doi.org/10.5281/zenodo.23609984)
[![ORCID: Vishal Chandel](https://img.shields.io/badge/ORCID-0009--0006--0552--8551-green.svg)](https://orcid.org/0009-0006-0552-8551)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 👥 Authors & Affiliations

* **Vishal Chandel** (Corresponding Author) — Department of Electronics & Communication, J.N.G.E.C., Sundernagar, Himachal Pradesh, India  
  *ORCID:* [`0009-0006-0552-8551`](https://orcid.org/0009-0006-0552-8551) | *Email:* `chandelvishal445@gmail.com`
* **Jyotiraditya Singh** — Department of Electronics & Communication, J.N.G.E.C., Sundernagar, Himachal Pradesh, India
* **Ajeet Thakur** (Co-Corresponding Author) — Department of Electronics & Communication, J.N.G.E.C., Sundernagar, Himachal Pradesh, India  
  *Email:* `ajeet.19eez0028@iitrpr.ac.in`

---

## 📌 Overview

Classical adaptive filters (LMS, NLMS, RLS, Kalman) provide point predictions without distribution-free confidence statements, while classical Variable Step-Size (VSS) schemes rely on error-power heuristics sensitive to noise scale and outliers.

**CCAF** addresses both challenges simultaneously:
1. **Distribution-Free Prediction Intervals:** Integrates online Adaptive Conformal Inference (ACI) to yield rigorous long-run marginal coverage bounds $\mathcal{O}(1/(\gamma T))$ for arbitrary, non-Gaussian observation sequences.
2. **Coverage-Driven Step-Size Control:** Closes the control loop by utilizing empirical nonconformity coverage misses as an intrinsic, scale-invariant feedback signal to dynamically modulate the filter step size $\mu(n)$.

```
   u(n) ---> [ Filter w(n) ] --------> y_hat(n) ------------> Prediction Interval: [y_hat ± q(n)*s(n)]
                   ^                        |
                   |                        v
                   |                   e(n) = d(n) - y_hat(n)
                   |                        |
                   |                        v
             Step Size μ(n) <--- Conformal ACI Layer <--- Nonconformity Score r(n) = |e(n)|/s(n)
```

---

## 🗂️ Repository Structure

```text
├── src/
│   ├── conformal/
│   │   └── ccaf.py                 # Core CCAF & Decoupled ACI-NLMS implementations
│   ├── filters/
│   │   └── baselines.py            # LMS, NLMS, RLS, APA, Kwong VSS, Benesty VSS, Convex Comb, Kalman
│   ├── data/
│   │   ├── synthetic.py            # Synthetic scenario generator (S1 to S6)
│   │   ├── air_loader.py           # Aachen Impulse Response (AIR 1.4) data loader & AEC generator
│   │   ├── biomedical_loader.py    # MIT-BIH ECG & EEGdenoiseNet loaders
│   │   └── download_real_data.py   # Automated data downloader (PhysioNet & EEGdenoiseNet)
│   ├── metrics/
│   │   ├── evaluator.py            # MSD, EMSE, empirical coverage, Winkler score
│   │   └── stats_protocol.py       # Wilcoxon signed-rank, Cliff's delta, Holm-Bonferroni, Clopper-Pearson CIs
│   └── experiments/
│       ├── run_s3_benchmark.py     # Scenario S3 abrupt plant change benchmark
│       ├── run_monte_carlo.py      # Monte Carlo campaigns across S1, S3, S5, S6
│       ├── run_ablations.py        # Hyperparameter sensitivity (gamma, control exponent p)
│       ├── run_air_benchmark.py    # Aachen AIR acoustic echo cancellation benchmark
│       ├── run_s7_benchmark.py     # Real-world ECG and EEG biomedical benchmarks
│       ├── run_stats_pipeline.py   # Statistical significance and ranking tests
│       └── generate_all_plots.py   # Generates all publication-ready figures
├── data/
│   ├── air/                        # Aachen Impulse Response Database files (AIR 1.4)
│   ├── ecg/                        # MIT-BIH Arrhythmia & Noise Stress Test Database (NSTDB)
│   └── eeg/                        # EEGdenoiseNet ocular artifact epochs
├── results/                        # Generated benchmark figures (.png) and stats (.json)
├── run_all.py                      # Master one-command reproduction pipeline
├── create_paper_docx.py            # Generates the complete IEEE single-column research paper (.docx)
├── IMPLEMENTATION_CHECKLIST.md     # Full development and validation checklist
└── requirements.txt                # Python dependencies
```

---

## 🚀 Quick Start

### 1. Installation

Clone this repository and install dependencies:

```bash
git clone https://github.com/Vishal442005/Conformal_Controlled_Adaptive_Filtering.git
cd Conformal_Controlled_Adaptive_Filtering
pip install -r requirements.txt
```

### 2. Android Edge Mobile Application (v1.2.0)

For mobile edge deployment and real-time acoustic demonstration, download the signed release APK:
* **Direct APK Download:** [`android_app/CCAF_Adaptive_Filter_v1.2.0.apk`](android_app/CCAF_Adaptive_Filter_v1.2.0.apk)
* **Features:**
  - Real-time live audio recording with dual-channel acoustic echo cancellation & noise suppression
  - File-based processing (.wav) with side-by-side audio playback comparison (Original vs. Filtered)
  - Interactive Model Selector supporting:
    - **CCAF Dead-Band (Proposed)** — Distribution-free coverage-driven step-size control
    - **Benesty Non-Parametric VSS** — Power-ratio variable step-size
    - **Convex Combination Filter** — Fast/slow convex filter mixture
    - **Kwong VSS** — Squared-error variable step-size
    - **NLMS (Fast & Slow)** — Standard normalized LMS baselines
  - Custom model configuration import/export (.json)

### 3. Download Datasets (Optional if already extracted in `data/`)

To automatically fetch real-world data (MIT-BIH ECG and EEGdenoiseNet):
```bash
python src/data/download_real_data.py
```
*Note: The Aachen Impulse Response Database is located under `data/air/AIR_1_4/`.*

### 4. Run Everything (One-Command Reproduction)

To execute the entire simulation suite, benchmarks, ablations, and generate all result plots:
```bash
python run_all.py
```

All plots will be output directly to the [`results/`](results/) folder.

---

## 🧪 Experimental Benchmarks

| Scenario | Type | Description | Evaluated Claims |
| :--- | :--- | :--- | :--- |
| **S1** | Synthetic | Stationary Gaussian noise ($\text{SNR}=20\text{ dB}$, white input) | C2 (Nominal efficiency matches Kalman oracle) |
| **S2** | Synthetic | Coloured $\text{AR}(1)$ input with $\rho = 0.95$ (eigenvalue spread) | Robustness under ill-conditioned autocorrelation |
| **S3** | Synthetic | Abrupt plant change (sign-flip $w_o \to -w_o$ at $n=4000$) | C3 (Detection delay & fast re-convergence) |
| **S4** | Synthetic | Random-walk plant drift ($\sigma_q = 5\times 10^{-4}$) | Tracking optimality vs. Kalman filter |
| **S5** | Synthetic | Time-varying noise variance jumps ($10\times$ power jump) | Running scale adaptation & interval validity |
| **S6** | Synthetic | Non-Gaussian heavy tails (Student-$t$ with $\nu=3$, 10% outliers) | C4 (Distribution-free coverage under outliers) |
| **S7a** | Real-world | MIT-BIH ECG + Electrode Motion (EM) noise | Clinical ECG artifact cancellation |
| **S7b** | Real-world | EEGdenoiseNet ocular artifact (EOG) removal | 53.9% error reduction vs. standard NLMS |
| **S7c** | Real-world | Aachen Impulse Response (AIR 1.4) in Aula Carolina auditorium | Real-world Acoustic Echo Cancellation (AEC) |

---

## 📊 Individual Experiment Scripts

You can also run specific scenarios individually:

* **Scenario S3 (Plant change tracking & coverage):**
  ```bash
  python src/experiments/run_s3_benchmark.py
  ```
* **Monte Carlo Campaigns (S1, S3, S5, S6):**
  ```bash
  python src/experiments/run_monte_carlo.py
  ```
* **Acoustic Echo Cancellation (Aachen AIR Database):**
  ```bash
  python src/experiments/run_air_benchmark.py
  ```
* **Biomedical Benchmarks (MIT-BIH ECG & EEGdenoiseNet):**
  ```bash
  python src/experiments/run_s7_benchmark.py
  ```
* **Hyperparameter Sensitivity & Ablations:**
  ```bash
  python src/experiments/run_ablations.py
  ```
* **Statistical Significance Pipeline:**
  ```bash
  python src/experiments/run_stats_pipeline.py
  ```

---

## 📄 Generating the IEEE Research Paper Manuscript

To regenerate the complete, formatted manuscript containing all 9 tables, 12 figures, and theoretical derivations in IEEE single-column format:
```bash
python create_paper_docx.py
```
This generates:
* `Conformal_Controlled_Adaptive_Filtering_IEEE_SingleColumn_Final.docx`

---

## 📈 Key Results Summary

* **Marginal Coverage:** Strictly preserves nominal 90% coverage across all regimes (empirical coverage: **88.5% – 89.6%** within exact Clopper-Pearson 95% confidence intervals).
* **Interval Sharpness (Winkler Score):** Up to **32% improvement** in interval sharpness over decoupled ACI baselines during non-stationary transitions.
* **Acoustic Echo Cancellation (AIR):** Reaches steady-state tracking of **-15.76 dB** MSD on real room impulse responses, outperforming slow NLMS (-8.73 dB), Kwong VSS-LMS (-5.44 dB), and Benesty NP-VSS (-12.01 dB).
* **Statistical Significance:** Paired Wilcoxon signed-rank tests show statistically decisive superiority over competitors ($p_{\text{adj}} < 10^{-10}$, Cliff's Delta $= +1.0$).

---

## 📜 Citation

If you find this code, benchmark suite, or research useful in your work, please cite:

```bibtex
@software{chandel2026ccaf,
  author       = {Chandel, Vishal and Singh, Jyotiraditya and Thakur, Ajeet},
  title        = {{Conformal-Controlled Adaptive Filtering: Distribution-Free Uncertainty Bounds and Coverage-Driven Step-Size Control}},
  month        = nov,
  year         = 2026,
  publisher    = {Zenodo},
  version      = {v1.2.0},
  doi          = {10.5281/zenodo.23609984},
  url          = {https://doi.org/10.5281/zenodo.23609984}
}

@article{chandel2026conformal,
  title        = {Conformal-Controlled Adaptive Filtering: Distribution-Free Uncertainty Bounds and Coverage-Driven Step-Size Control},
  author       = {Chandel, Vishal and Singh, Jyotiraditya and Thakur, Ajeet},
  journal      = {IEEE Transactions on Signal Processing (Under Review)},
  year         = {2026}
}
```

---

## ⚖️ License

Distributed under the MIT License. See `LICENSE` for more information.
