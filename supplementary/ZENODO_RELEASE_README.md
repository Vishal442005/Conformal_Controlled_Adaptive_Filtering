# Supplementary Material & Zenodo Archive
## Conformal-Controlled Adaptive Filtering: Distribution-Free Guarantees and Coverage-Driven Step-Size Control

- **Authors:**
  - **Vishal Chandel** (ORCID: [0009-0006-0552-8551](https://orcid.org/0009-0006-0552-8551), Email: `chandelvishal445@gmail.com`)
  - **Jyotiraditya Singh** (Department of Electronics & Communication, J.N.G.E.C., Sundernagar, HP, India)
  - **Ajeet Thakur** (Email: `ajeet.19eez0028@iitrpr.ac.in`)
- **Version:** v1.2.0
- **Release Date:** November 2026
- **Persistent Archive DOI:** [10.5281/zenodo.23609984](https://doi.org/10.5281/zenodo.23609984)
- **Active Open-Source Repository:** [https://github.com/Vishal442005/Conformal_Controlled_Adaptive_Filtering](https://github.com/Vishal442005/Conformal_Controlled_Adaptive_Filtering)
- **License:** MIT License
- **Mobile Edge Demonstrator:** Android APK v1.2.0 (`android_app/CCAF_Adaptive_Filter_v1.2.0.apk`)

---

### Archive Contents

```text
supplementary/
├── figures_pdf/                           # 300-DPI vector-grade publication figures
│   ├── fig_ccaf_architecture.pdf          # Fig 1: Standalone system block architecture
│   ├── fig_ccaf_flowchart.pdf             # Fig 2: Standalone procedural execution flowchart
│   ├── fig_conformal_calibration_and_reliability.pdf  # Conformal calibration & reliability
│   ├── fig_state_space_phase_portrait.pdf # Dynamical phase-plane & attractor map
│   ├── fig_hyperparameter_landscape_nomogram.pdf # 2D parameter operational nomogram
│   ├── fig_multicriteria_radar_benchmark.pdf     # 6-axis multi-criteria radar footprint
│   ├── fig_acoustic_rir_energy_decay_and_tracking.pdf # Measured AIR RIR, EDC & speech tracking
│   └── ... (all Monte Carlo, Ablation & Benchmark PDFs)
├── figures_png/                           # High-res 300-DPI PNG renderings
├── animations/
│   └── quantile_tracking_animation.gif    # Dynamic error quantile envelope tracking animation
├── scripts/                               # Core Python implementation and analysis scripts
│   ├── ccaf.py                            # CCAF & Decoupled ACI-NLMS algorithms
│   ├── baselines.py                       # Classical & variable step-size benchmarks
│   ├── generate_deep_understanding_visuals.py # Diagnostic & attractor plotting
│   ├── generate_acoustic_rir_diagnostics.py  # Acoustic RIR & animation generator
│   └── run_all.py                         # Master one-click reproduction pipeline
└── ZENODO_RELEASE_README.md               # This archive manifest
```

---

### One-Click Reproduction Instructions

1. **Install Prerequisites**:
   ```bash
   pip install -r scripts/requirements.txt
   ```

2. **Run Master Experimental Suite**:
   ```bash
   python scripts/run_all.py
   ```

3. **Generate All Deep-Understanding Diagnostic Figures**:
   ```bash
   python scripts/generate_deep_understanding_visuals.py
   python scripts/generate_acoustic_rir_diagnostics.py
   ```

All simulation results, statistical tables, and publication-grade figures will be reproduced identically with seeded pseudo-random number generators.
