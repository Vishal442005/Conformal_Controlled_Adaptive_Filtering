"""
package_zenodo_supplementary.py
Packages all experimental scripts, publication-grade figures, animations,
and documentation for the Zenodo Release (DOI: 10.5281/zenodo.23609984)
and Supplementary Material submission.
"""

import os
import shutil
import zipfile

def create_supplementary_package():
    print("=" * 80)
    print("PACKAGING ZENODO RELEASE & SUPPLEMENTARY MATERIAL")
    print("DOI: 10.5281/zenodo.23609984")
    print("=" * 80)

    supp_dir = os.path.abspath("supplementary")
    os.makedirs(supp_dir, exist_ok=True)
    os.makedirs(os.path.join(supp_dir, "figures_pdf"), exist_ok=True)
    os.makedirs(os.path.join(supp_dir, "figures_png"), exist_ok=True)
    os.makedirs(os.path.join(supp_dir, "animations"), exist_ok=True)
    os.makedirs(os.path.join(supp_dir, "scripts"), exist_ok=True)

    # 1. Copy Key Figures (PDF & PNG)
    results_dir = os.path.abspath("results")
    for f in os.listdir(results_dir):
        if f.endswith(".pdf"):
            shutil.copy2(os.path.join(results_dir, f), os.path.join(supp_dir, "figures_pdf", f))
        elif f.endswith(".png") and not f.startswith("frame_"):
            shutil.copy2(os.path.join(results_dir, f), os.path.join(supp_dir, "figures_png", f))
        elif f.endswith(".gif"):
            shutil.copy2(os.path.join(results_dir, f), os.path.join(supp_dir, "animations", f))

    # 2. Copy Analysis and Visualization Scripts
    scripts_to_copy = [
        "src/experiments/generate_deep_understanding_visuals.py",
        "src/experiments/generate_acoustic_rir_diagnostics.py",
        "src/experiments/run_s3_benchmark.py",
        "src/experiments/run_monte_carlo.py",
        "src/experiments/run_ablations.py",
        "src/experiments/run_air_benchmark.py",
        "src/experiments/run_s7_benchmark.py",
        "src/experiments/run_stats_pipeline.py",
        "src/conformal/ccaf.py",
        "src/filters/baselines.py",
        "run_all.py",
        "requirements.txt"
    ]
    for s in scripts_to_copy:
        if os.path.exists(s):
            dest_name = os.path.basename(s)
            shutil.copy2(s, os.path.join(supp_dir, "scripts", dest_name))

    # 3. Create Detailed Supplementary Guide
    readme_path = os.path.join(supp_dir, "ZENODO_RELEASE_README.md")
    with open(readme_path, "w", encoding="utf-8") as rf:
        rf.write("""# Supplementary Material & Zenodo Archive
## Conformal-Controlled Adaptive Filtering: Distribution-Free Guarantees and Coverage-Driven Step-Size Control

- **Persistent Archive DOI:** [10.5281/zenodo.23609984](https://doi.org/10.5281/zenodo.23609984)
- **Active Open-Source Repository:** [https://github.com/Vishal442005/Conformal_Controlled_Adaptive_Filtering](https://github.com/Vishal442005/Conformal_Controlled_Adaptive_Filtering)
- **License:** MIT License

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
""")

    # 4. Create Standalone ZIP Archive
    zip_path = os.path.join(results_dir, "CCAF_Zenodo_Supplementary_Package.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(supp_dir):
            for file in files:
                f_full = os.path.join(root, file)
                rel_path = os.path.relpath(f_full, supp_dir)
                zipf.write(f_full, os.path.join("CCAF_Supplementary_Material", rel_path))

    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"[SUCCESS] Zenodo Supplementary Package created at:\n  {zip_path} ({size_mb:.2f} MB)")
    print(f"[SUCCESS] Supplementary directory populated at:\n  {supp_dir}")

if __name__ == "__main__":
    create_supplementary_package()
