"""
generate_acoustic_rir_diagnostics.py
Generates:
1. fig_acoustic_rir_energy_decay_and_tracking.png / .pdf
   - Panel (a): Measured Binaural Room Impulse Response (AIR 1.4 Aula Carolina) vs CCAF-DB converged weights
   - Panel (b): Spatial Energy Decay Curve (EDC) / Schroeder Integration (dB) across delay
   - Panel (c): Dynamic Conformal Quantile Tracking over Real Speech / Acoustic Envelopes
2. quantile_tracking_animation.gif (Supplementary Material animation)
   - Animated visual tracking of adaptive error quantile bounds over streaming non-stationary acoustic signals
"""

import os
import sys
sys.path.insert(0, os.path.abspath("."))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image

from src.data.air_loader import load_air_impulse_response, generate_aec_simulation_data
from src.conformal.ccaf import CCAF
from src.filters.baselines import NLMSFilter, BenestyNPVSSNLMS

# Publication Styling
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['mathtext.fontset'] = 'cm'
plt.rcParams['axes.edgecolor'] = '#1E293B'
plt.rcParams['axes.linewidth'] = 1.0

RESULTS_DIR = os.path.abspath("results")
LATEX_FIG_DIR = os.path.abspath("paper_latex/figures")
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(LATEX_FIG_DIR, exist_ok=True)

def schroeder_edc(w):
    """
    Compute energy decay curve (EDC) in dB via Schroeder backward integration:
    EDC(t) = 10 * log10( sum_{tau=t}^M w^2(tau) / sum_{tau=0}^M w^2(tau) )
    """
    w2 = w ** 2
    cum_energy = np.cumsum(w2[::-1])[::-1]
    total_energy = cum_energy[0] + 1e-12
    edc_linear = cum_energy / total_energy
    edc_db = 10.0 * np.log10(np.maximum(edc_linear, 1e-6))
    return edc_db

def render_acoustic_rir_diagnostics():
    print("[1/2] Generating Acoustic RIR Spatial Energy Decay & Conformal Tracking Diagnostics...")
    air_file = os.path.abspath("data/air/AIR_1_4/air_binaural_aula_carolina_0_1_1_90_3.mat")
    air_file_ch = os.path.abspath("data/air/AIR_1_4/air_binaural_aula_carolina_0_1_2_90_3.mat")
    
    num_taps = 128
    num_samples = 12000
    change_sample = 6000
    fs = 16000  # 16 kHz sampling rate
    time_ms = np.arange(num_taps) / (fs / 1000.0)

    # Generate AEC simulation data with measured Aula Carolina AIR
    data = generate_aec_simulation_data(
        air_path_initial=air_file,
        air_path_changed=air_file_ch,
        num_samples=num_samples,
        num_taps=num_taps,
        snr_db=25.0,
        change_sample=change_sample,
        seed=101
    )
    U, d, W_opt = data["U"], data["d"], data["W_opt"]

    # Run CCAF-DB
    f_ccaf = CCAF(num_taps=num_taps, alpha=0.10, gamma=0.02, mu_min=0.03, mu_max=0.8, tau=0.03)
    res_ccaf = f_ccaf.run(U, d)

    # Run Baselines
    f_nlms = NLMSFilter(num_taps=num_taps, mu=0.05)
    res_nlms = f_nlms.run(U, d)

    f_benesty = BenestyNPVSSNLMS(num_taps=num_taps)
    res_benesty = f_benesty.run(U, d)

    # Final converged weights before plant change (at n = 5800)
    w_true = W_opt[5800]
    w_ccaf = res_ccaf["W_history"][5800]
    w_nlms = res_nlms["W_history"][5800]
    w_benesty = res_benesty["W_history"][5800]

    # Compute Energy Decay Curves (EDC)
    edc_true = schroeder_edc(w_true)
    edc_ccaf = schroeder_edc(w_ccaf)
    edc_nlms = schroeder_edc(w_nlms)
    edc_benesty = schroeder_edc(w_benesty)

    # Create 3-Panel Figure
    fig, axes = plt.subplots(1, 3, figsize=(16.8, 5.2))

    # PANEL A: Measured RIR vs Converged Weights
    ax1 = axes[0]
    ax1.plot(time_ms, w_true, color='#0F172A', lw=1.8, label="Aachen AIR True Profile ($w_o$)")
    ax1.plot(time_ms, w_ccaf, color='#0284C7', lw=1.6, linestyle='--', label=r"CCAF-DB Estimated ($\hat{w}$)")
    
    # Highlight acoustic regions
    ax1.axvspan(0, 1.2, color='#FEF3C7', alpha=0.6, label="Direct Acoustic Path")
    ax1.axvspan(1.2, 4.0, color='#E0E7FF', alpha=0.5, label="Early Room Reflections")
    ax1.axvspan(4.0, time_ms[-1], color='#F1F5F9', alpha=0.5, label="Late Reverberant Tail")

    ax1.set_xlim(0, time_ms[-1])
    ax1.set_xlabel("Time Delay (ms)", fontsize=11.5, fontweight='bold')
    ax1.set_ylabel("Normalized Amplitude", fontsize=11.5, fontweight='bold')
    ax1.set_title("(a) Measured Binaural RIR vs. Filter Tap Weights", fontsize=12.5, fontweight='bold')
    ax1.grid(True, linestyle=':', alpha=0.5)
    ax1.legend(loc='upper right', fontsize=8.5, framealpha=0.92)

    # PANEL B: Schroeder Spatial Energy Decay Curve (EDC)
    ax2 = axes[1]
    ax2.plot(time_ms, edc_true, color='#0F172A', lw=2.2, label="True Room Decay Profile")
    ax2.plot(time_ms, edc_ccaf, color='#0284C7', lw=2.0, linestyle='-', label="CCAF-DB (Proposed)")
    ax2.plot(time_ms, edc_benesty, color='#8E44AD', lw=1.7, linestyle='-.', label="Benesty NP-VSS")
    ax2.plot(time_ms, edc_nlms, color='#64748B', lw=1.6, linestyle=':', label="Slow Fixed NLMS")

    ax2.set_xlim(0, time_ms[-1])
    ax2.set_ylim(-45, 2)
    ax2.set_xlabel("Decay Time (ms)", fontsize=11.5, fontweight='bold')
    ax2.set_ylabel("Spatial Energy Decay EDC (dB)", fontsize=11.5, fontweight='bold')
    ax2.set_title("(b) Schroeder Energy Decay Dynamic Profile", fontsize=12.5, fontweight='bold')
    ax2.grid(True, linestyle=':', alpha=0.5)
    ax2.legend(loc='lower left', fontsize=9.0, framealpha=0.92)

    # PANEL C: Speech Phoneme Segment & Dynamic Conformal Quantile Bounds
    ax3 = axes[2]
    # Zoom in around speech active segment (e.g., n = 4500 to 5200)
    w_zoom = np.arange(4600, 5100)
    t_zoom_ms = (w_zoom - w_zoom[0]) / (fs / 1000.0)

    d_seg = d[w_zoom]
    y_low = res_ccaf["y_lower"][w_zoom]
    y_upp = res_ccaf["y_upper"][w_zoom]
    y_pred = (y_low + y_upp) / 2.0

    ax3.fill_between(t_zoom_ms, y_low, y_upp, color='#38BDF8', alpha=0.35,
                     label=r"Dynamic Conformal $90\%$ Band $[\hat{y} \pm q\cdot s]$")
    ax3.plot(t_zoom_ms, d_seg, color='#0F172A', lw=1.4, label="Desired Signal $d(n)$ (Speech Echo)")
    ax3.plot(t_zoom_ms, y_pred, color='#0284C7', lw=1.6, linestyle='--', label=r"Adaptive Filter Output $\hat{y}(n)$")

    ax3.set_xlim(t_zoom_ms[0], t_zoom_ms[-1])
    ax3.set_xlabel("Segment Duration (ms)", fontsize=11.5, fontweight='bold')
    ax3.set_ylabel("Signal Amplitude", fontsize=11.5, fontweight='bold')
    ax3.set_title("(c) Causal Speech Envelopes & Dynamic Quantile Tracking", fontsize=12.5, fontweight='bold')
    ax3.grid(True, linestyle=':', alpha=0.5)
    ax3.legend(loc='upper right', fontsize=8.5, framealpha=0.92)

    plt.tight_layout()
    out_png = os.path.join(RESULTS_DIR, "fig_acoustic_rir_energy_decay_and_tracking.png")
    out_pdf = os.path.join(RESULTS_DIR, "fig_acoustic_rir_energy_decay_and_tracking.pdf")
    fig.savefig(out_png, dpi=300, bbox_inches='tight')
    fig.savefig(out_pdf, bbox_inches='tight')
    fig.savefig(os.path.join(LATEX_FIG_DIR, "fig_acoustic_rir_energy_decay_and_tracking.png"), dpi=300, bbox_inches='tight')
    fig.savefig(os.path.join(LATEX_FIG_DIR, "fig_acoustic_rir_energy_decay_and_tracking.pdf"), bbox_inches='tight')
    plt.close(fig)
    print("  [SAVED] fig_acoustic_rir_energy_decay_and_tracking (PNG & PDF)")


def render_error_quantile_animation():
    print("[2/2] Generating Animated Quantile Tracking Sequence (GIF for Supplementary Release)...")
    num_taps = 16
    num_samples = 4000
    change_sample = 2000

    from src.data.synthetic import generate_synthetic_data
    data = generate_synthetic_data("S3", num_taps=num_taps, num_samples=num_samples,
                                   step_change_sample=change_sample, snr_db=20.0, seed=42)
    U, d = data["U"], data["d"]

    f = CCAF(num_taps=num_taps, alpha=0.10, gamma=0.02, mu_min=0.05, mu_max=0.8, tau=0.02)
    res = f.run(U, d)

    d_sig = d
    y_low = res["y_lower"]
    y_upp = res["y_upper"]
    mu_hist = res["mu_hist"]
    e_hist = res["e"]

    # Select window around plant change: n = 1800 to 2400
    frames_dir = os.path.join(RESULTS_DIR, "animation_frames")
    os.makedirs(frames_dir, exist_ok=True)

    window_size = 250
    step = 10
    start_indices = range(1750, 2350, step)
    frame_paths = []

    for idx_num, start_idx in enumerate(start_indices):
        end_idx = start_idx + window_size
        sub_n = np.arange(start_idx, end_idx)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9.5, 5.0), gridspec_kw={'height_ratios': [2.2, 1.2]}, dpi=100)

        # Top: Signal and Quantile Envelopes
        ax1.fill_between(sub_n, y_low[sub_n], y_upp[sub_n], color='#38BDF8', alpha=0.4, label="Conformal 90% Envelope")
        ax1.plot(sub_n, d_sig[sub_n], color='#0F172A', lw=1.2, label="Desired Signal d(n)")
        ax1.plot(sub_n, (y_low[sub_n] + y_upp[sub_n])/2.0, color='#0284C7', lw=1.5, linestyle='--', label=r"Prediction $\hat{y}(n)$")
        
        if start_idx <= change_sample < end_idx:
            ax1.axvline(change_sample, color='#EF4444', lw=2.0, linestyle='--', label="Plant Disruption")

        ax1.set_xlim(start_idx, end_idx)
        ax1.set_ylim(-3.5, 3.5)
        ax1.set_ylabel("Signal / Target", fontsize=10.5, fontweight='bold')
        ax1.set_title(f"Real-Time Conformal Quantile Tracking (Frame {idx_num+1}/{len(start_indices)} | Iteration n={end_idx})",
                      fontsize=11.5, fontweight='bold')
        ax1.grid(True, linestyle=':', alpha=0.5)
        ax1.legend(loc='upper right', fontsize=8.0, framealpha=0.9)

        # Bottom: Adaptive Step Size mu(n)
        ax2.plot(sub_n, mu_hist[sub_n], color='#DC2626', lw=1.8, label=r"Adaptive Step Size $\mu(n)$")
        ax2.axhline(0.05, color='#10B981', lw=1.2, linestyle=':', label=r"$\mu_{\min}$ Floor")
        ax2.set_xlim(start_idx, end_idx)
        ax2.set_ylim(0.0, 0.85)
        ax2.set_xlabel("Iteration Index ($n$)", fontsize=10.5, fontweight='bold')
        ax2.set_ylabel(r"$\mu(n)$", fontsize=10.5, fontweight='bold')
        ax2.grid(True, linestyle=':', alpha=0.5)
        ax2.legend(loc='upper right', fontsize=8.0, framealpha=0.9)

        plt.tight_layout()
        f_path = os.path.join(frames_dir, f"frame_{idx_num:03d}.png")
        fig.savefig(f_path, bbox_inches='tight')
        plt.close(fig)
        frame_paths.append(f_path)

    # Save animated GIF using PIL
    gif_path = os.path.join(RESULTS_DIR, "quantile_tracking_animation.gif")
    images = [Image.open(p) for p in frame_paths]
    if images:
        images[0].save(gif_path, save_all=True, append_images=images[1:], duration=80, loop=0)
        print(f"  [SAVED] Animated GIF saved at: {gif_path} ({len(images)} frames)")

if __name__ == "__main__":
    print("=" * 80)
    print("ACOUSTIC RIR & ERROR QUANTILE TRACKING DIAGNOSTICS GENERATOR")
    print("=" * 80)
    render_acoustic_rir_diagnostics()
    render_error_quantile_animation()
    print("=" * 80)
    print("ACOUSTIC DIAGNOSTICS & ANIMATION GENERATION COMPLETE!")
    print("=" * 80)
