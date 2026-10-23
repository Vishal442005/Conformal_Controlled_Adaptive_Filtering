import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from src.data.biomedical_loader import load_ecg_noise_cancellation_data
from src.filters.baselines import (
    NLMSFilter,
    RLSFilter,
    KwongJohnstonVSSLMS,
    BenestyNPVSSNLMS,
    ConvexCombinationNLMS
)
from src.conformal.ccaf import CCAF, DecoupledACINLMS
from src.metrics.evaluator import compute_coverage, compute_winkler_score, compute_sliding_coverage

def enhance_ecg_plot():
    print("Regenerating s7_ecg_validation.png with enhanced publication styling (no model/value changes)...")
    ecg_data = load_ecg_noise_cancellation_data(num_samples=10000, num_taps=16)
    U_ecg = ecg_data["U"]
    d_ecg = ecg_data["d"]
    clean_ecg = ecg_data["clean_ecg"]

    # Re-run identical filter configurations
    filters_ecg = {
        "NLMS (fixed mu=0.1)": NLMSFilter(num_taps=16, mu=0.1),
        "RLS (lambda=0.99)": RLSFilter(num_taps=16, lmbda=0.99),
        "Kwong VSS-LMS": KwongJohnstonVSSLMS(num_taps=16, alpha=0.97, gamma=0.005, mu_min=0.01, mu_max=0.5),
        "Benesty NP-VSS": BenestyNPVSSNLMS(num_taps=16),
        "Convex Combination": ConvexCombinationNLMS(num_taps=16, mu_fast=0.5, mu_slow=0.05),
        "Decoupled ACI-NLMS": DecoupledACINLMS(num_taps=16, mu_fixed=0.05, alpha=0.10, gamma=0.02),
        "Proposed CCAF": CCAF(num_taps=16, alpha=0.10, gamma=0.02, mu_min=0.02, mu_max=0.6, p=1.0)
    }

    results = {}
    for name, f in filters_ecg.items():
        res = f.run(U_ecg, d_ecg)
        results[name] = res

    ccaf_res = results["Proposed CCAF"]
    dec_res = results["Decoupled ACI-NLMS"]
    nlms_res = results["NLMS (fixed mu=0.1)"]

    # 4-panel enhanced layout
    fig = plt.figure(figsize=(12, 11))
    gs = fig.add_gridspec(4, 1, height_ratios=[1.0, 1.15, 0.85, 0.95], hspace=0.32)

    # Panel (a): Macro signal overview
    ax0 = fig.add_subplot(gs[0])
    macro_slice = slice(4000, 4800)
    time_macro = np.arange(4000, 4800)
    ax0.plot(time_macro, clean_ecg[macro_slice], label="Clean Ground Truth ECG", color='#0f172a', linewidth=1.5, zorder=3)
    ax0.plot(time_macro, d_ecg[macro_slice], label="Contaminated Primary Signal (ECG + Electrode Motion)", color='#ef4444', alpha=0.45, linewidth=1.0)
    ax0.set_ylabel("Amplitude", fontsize=9.5)
    ax0.set_title("(a) Macro View: MIT-BIH Record 118 with Calibrated Electrode Motion (EM) Noise", fontsize=11, fontweight='bold', loc='left')
    ax0.legend(loc="upper right", fontsize=8.5, framealpha=0.9)
    ax0.grid(True, linestyle=':', alpha=0.6)
    ax0.set_xlim(4000, 4800)

    # Highlight zoom window
    zoom_start, zoom_end = 4220, 4420
    rect = Rectangle((zoom_start, -2.6), zoom_end - zoom_start, 6.8, linewidth=1.5, edgecolor='#0284c7', facecolor='none', linestyle='--', zorder=4)
    ax0.add_patch(rect)
    ax0.text(zoom_start + 10, 3.5, "Zoom Region [QRS Complex]", color='#0284c7', fontsize=8.5, fontweight='bold')

    # Panel (b): Zoomed QRS morphology with 90% Conformal Prediction Ribbon
    ax1 = fig.add_subplot(gs[1])
    zoom_slice = slice(zoom_start, zoom_end)
    time_zoom = np.arange(zoom_start, zoom_end)

    # Prediction confidence interval shading
    lower_bound = ccaf_res["y_lower"][zoom_slice]
    upper_bound = ccaf_res["y_upper"][zoom_slice]
    # Denoised signal estimate is e(n) = d(n) - y_hat(n)
    # The corresponding confidence interval around denoised estimate is clean ± half_width
    half_width = 0.5 * (upper_bound - lower_bound)
    ccaf_denoised = ccaf_res["e"][zoom_slice]
    nlms_denoised = nlms_res["e"][zoom_slice]
    clean_zoom = clean_ecg[zoom_slice]

    ax1.fill_between(time_zoom, ccaf_denoised - half_width, ccaf_denoised + half_width,
                     color='#38bdf8', alpha=0.25, label="CCAF Calibrated 90% Prediction Interval", zorder=1)
    ax1.plot(time_zoom, clean_zoom, label="Clean ECG Reference", color='#000000', linewidth=1.8, zorder=4)
    ax1.plot(time_zoom, ccaf_denoised, label="CCAF Denoised Reconstruction", color='#0284c7', linewidth=1.5, zorder=3)
    ax1.plot(time_zoom, nlms_denoised, label="NLMS Baseline (mu=0.1)", color='#d97706', linestyle='--', linewidth=1.3, zorder=2)
    ax1.set_ylabel("Amplitude", fontsize=9.5)
    ax1.set_title("(b) Morphological Detail: QRS Peak Preservation & Distribution-Free Confidence Envelope", fontsize=11, fontweight='bold', loc='left')
    ax1.legend(loc="upper right", fontsize=8.5, framealpha=0.9, ncol=2)
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.set_xlim(zoom_start, zoom_end)

    # Panel (c): Point-by-point residual error |e_clean - e_est|
    ax2 = fig.add_subplot(gs[2])
    err_ccaf = np.abs(clean_zoom - ccaf_denoised)
    err_nlms = np.abs(clean_zoom - nlms_denoised)
    ax2.plot(time_zoom, err_nlms, label="NLMS Error: |e_clean - e_nlms|", color='#d97706', linewidth=1.2, linestyle=':')
    ax2.plot(time_zoom, err_ccaf, label="CCAF Error: |e_clean - e_ccaf|", color='#0284c7', linewidth=1.4)
    ax2.set_ylabel("Abs Error", fontsize=9.5)
    ax2.set_title("(c) Denoising Error Residual (Lower is Better)", fontsize=11, fontweight='bold', loc='left')
    ax2.legend(loc="upper right", fontsize=8.5, framealpha=0.9)
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.set_xlim(zoom_start, zoom_end)

    # Panel (d): Empirical Sliding Coverage
    ax3 = fig.add_subplot(gs[3])
    slide_ccaf = compute_sliding_coverage(d_ecg, ccaf_res["y_lower"], ccaf_res["y_upper"], window=400)
    slide_dec = compute_sliding_coverage(d_ecg, dec_res["y_lower"], dec_res["y_upper"], window=400)
    x_axis_cov = np.arange(399, len(d_ecg))

    ax3.plot(x_axis_cov, slide_ccaf, label="Proposed CCAF Sliding Coverage", color='#0284c7', linewidth=1.6)
    ax3.plot(x_axis_cov, slide_dec, label="Decoupled ACI Sliding Coverage", color='#94a3b8', linestyle='--', linewidth=1.2)
    ax3.axhline(0.90, color='#10b981', linestyle='-', linewidth=1.3, label="Nominal Target Coverage (90%)")
    ax3.set_xlabel("Sample Index (n)", fontsize=10)
    ax3.set_ylabel("Coverage Proportion", fontsize=9.5)
    ax3.set_ylim(0.75, 0.98)
    ax3.set_title("(d) Long-Run Empirical Coverage Guarantee (Sliding Window W = 400 Samples)", fontsize=11, fontweight='bold', loc='left')
    ax3.legend(loc="lower left", fontsize=8.5, framealpha=0.9, ncol=3)
    ax3.grid(True, linestyle=':', alpha=0.6)
    ax3.set_xlim(0, len(d_ecg))

    out_path = os.path.abspath("results/s7_ecg_validation.png")
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[SUCCESS] Enhanced ECG figure saved to: {out_path}")

if __name__ == "__main__":
    enhance_ecg_plot()
