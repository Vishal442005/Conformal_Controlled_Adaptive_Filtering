import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from src.data.biomedical_loader import load_ecg_noise_cancellation_data, load_eeg_artifact_removal_data
from src.filters.baselines import (
    NLMSFilter,
    RLSFilter,
    KwongJohnstonVSSLMS,
    BenestyNPVSSNLMS,
    ConvexCombinationNLMS
)
from src.conformal.ccaf import CCAF, DecoupledACINLMS
from src.metrics.evaluator import compute_coverage, compute_winkler_score, compute_sliding_coverage

def run_s7_biomedical_validation():
    print("=" * 70)
    print("RUNNING SCENARIO S7: REAL-WORLD BIOMEDICAL VALIDATION")
    print("=" * 70)

    # -------------------------------------------------------------
    # 1. ECG Noise Stress Cancellation (MIT-BIH + NSTDB EM Noise)
    # -------------------------------------------------------------
    print("\n[Part 1] MIT-BIH Arrhythmia ECG + Electrode Motion (EM) Noise...")
    ecg_data = load_ecg_noise_cancellation_data(num_samples=10000, num_taps=16)
    U_ecg = ecg_data["U"]
    d_ecg = ecg_data["d"]
    clean_ecg = ecg_data["clean_ecg"]

    filters_ecg = {
        "NLMS (fixed mu=0.1)": NLMSFilter(num_taps=16, mu=0.1),
        "RLS (lambda=0.99)": RLSFilter(num_taps=16, lmbda=0.99),
        "Kwong VSS-LMS": KwongJohnstonVSSLMS(num_taps=16, alpha=0.97, gamma=0.005, mu_min=0.01, mu_max=0.5),
        "Benesty NP-VSS": BenestyNPVSSNLMS(num_taps=16),
        "Convex Combination": ConvexCombinationNLMS(num_taps=16, mu_fast=0.5, mu_slow=0.05),
        "Decoupled ACI-NLMS": DecoupledACINLMS(num_taps=16, mu_fixed=0.05, alpha=0.10, gamma=0.02),
        "Proposed CCAF": CCAF(num_taps=16, alpha=0.10, gamma=0.02, mu_min=0.02, mu_max=0.6, p=1.0)
    }

    results_ecg = {}
    for name, f in filters_ecg.items():
        print(f"  Filtering with {name}...")
        res = f.run(U_ecg, d_ecg)
        # In noise cancellation, filter error e(n) = d(n) - y_hat(n) is the denoised signal estimate
        denoised_ecg = res["e"]
        # Compute MSE with respect to true clean ECG
        mse = float(np.mean((denoised_ecg[2000:] - clean_ecg[2000:]) ** 2))
        results_ecg[name] = {
            "res": res,
            "mse": mse,
            "denoised": denoised_ecg
        }

    ccaf_ecg = results_ecg["Proposed CCAF"]["res"]
    dec_ecg = results_ecg["Decoupled ACI-NLMS"]["res"]

    cov_ecg_ccaf = compute_coverage(d_ecg, ccaf_ecg["y_lower"], ccaf_ecg["y_upper"])
    cov_ecg_dec = compute_coverage(d_ecg, dec_ecg["y_lower"], dec_ecg["y_upper"])
    wink_ecg_ccaf = compute_winkler_score(d_ecg, ccaf_ecg["y_lower"], ccaf_ecg["y_upper"])
    wink_ecg_dec = compute_winkler_score(d_ecg, dec_ecg["y_lower"], dec_ecg["y_upper"])

    print("\n--- ECG Denoising Performance ---")
    for name, r in results_ecg.items():
        print(f"  {name:<22}: Denoising MSE = {r['mse']:.4f}")
    print(f"  CCAF Coverage      : {cov_ecg_ccaf*100:.2f}% | Winkler Score: {wink_ecg_ccaf:.3f}")
    print(f"  Decoupled Coverage : {cov_ecg_dec*100:.2f}% | Winkler Score: {wink_ecg_dec:.3f}")

    # Plot ECG Results
    fig, axes = plt.subplots(3, 1, figsize=(11, 10), sharex=False)
    idx_slice = slice(4000, 4800)
    time_pts = np.arange(4000, 4800)

    ax = axes[0]
    ax.plot(time_pts, clean_ecg[idx_slice], label="Clean ECG (Ground Truth)", color='black', linewidth=1.5)
    ax.plot(time_pts, d_ecg[idx_slice], label="Noisy ECG (d = ECG + EM)", color='red', alpha=0.4)
    ax.set_ylabel("Amplitude")
    ax.set_title("ECG Noise Cancellation: Primary vs Clean ECG (MIT-BIH + NSTDB)")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    ax.plot(time_pts, clean_ecg[idx_slice], label="Clean ECG", color='black', alpha=0.7)
    ax.plot(time_pts, results_ecg["Proposed CCAF"]["denoised"][idx_slice], label="CCAF Denoised", color='blue', linewidth=1.5)
    ax.plot(time_pts, results_ecg["NLMS (fixed mu=0.1)"]["denoised"][idx_slice], label="NLMS Denoised", color='orange', linestyle='--', alpha=0.8)
    ax.set_ylabel("Amplitude")
    ax.set_title("Denoised ECG Comparison: CCAF vs Standard NLMS")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    ax = axes[2]
    slide_ccaf = compute_sliding_coverage(d_ecg, ccaf_ecg["y_lower"], ccaf_ecg["y_upper"], window=400)
    slide_dec = compute_sliding_coverage(d_ecg, dec_ecg["y_lower"], dec_ecg["y_upper"], window=400)
    ax.plot(np.arange(399, len(d_ecg)), slide_ccaf, label="CCAF Sliding Coverage", color='blue')
    ax.plot(np.arange(399, len(d_ecg)), slide_dec, label="Decoupled ACI Sliding Coverage", color='gray', linestyle='--')
    ax.axhline(0.90, color='green', linestyle=':', label="Target 90% Nominal Coverage")
    ax.set_xlabel("Sample Index (n)")
    ax.set_ylabel("Coverage Proportion")
    ax.set_ylim(0.70, 1.0)
    ax.set_title("Conformal Prediction Interval Coverage under Real ECG Electrode Artifacts")
    ax.legend(loc="lower left")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("results/s7_ecg_validation.png", dpi=250)
    plt.close()
    print("  [SAVED] results/s7_ecg_validation.png")

    # -------------------------------------------------------------
    # 2. EEGdenoiseNet Ocular Artifact Cancellation
    # -------------------------------------------------------------
    print("\n[Part 2] EEGdenoiseNet Ocular Artifact Removal...")
    eeg_data = load_eeg_artifact_removal_data(epoch_idx=5, snr_db=-2.0, num_taps=16)
    U_eeg = eeg_data["U"]
    d_eeg = eeg_data["d"]
    clean_eeg = eeg_data["clean_eeg"]

    ccaf_eeg_filter = CCAF(num_taps=16, alpha=0.10, gamma=0.03, mu_min=0.02, mu_max=0.6)
    nlms_eeg_filter = NLMSFilter(num_taps=16, mu=0.1)

    res_ccaf_eeg = ccaf_eeg_filter.run(U_eeg, d_eeg)
    res_nlms_eeg = nlms_eeg_filter.run(U_eeg, d_eeg)

    mse_ccaf_eeg = float(np.mean((res_ccaf_eeg["e"][500:] - clean_eeg[500:]) ** 2))
    mse_nlms_eeg = float(np.mean((res_nlms_eeg["e"][500:] - clean_eeg[500:]) ** 2))
    cov_eeg = compute_coverage(d_eeg, res_ccaf_eeg["y_lower"], res_ccaf_eeg["y_upper"])

    print(f"  CCAF EEG Denoising MSE: {mse_ccaf_eeg:.4f}")
    print(f"  NLMS EEG Denoising MSE: {mse_nlms_eeg:.4f}")
    print(f"  CCAF EEG Conformal Coverage: {cov_eeg*100:.2f}% (Nominal 90%)")

    # Plot EEG Results
    plt.figure(figsize=(10, 6))
    time_pts = np.arange(len(clean_eeg))
    plt.plot(time_pts[:600], d_eeg[:600], label="Contaminated EEG (EEG + EOG)", color='red', alpha=0.4)
    plt.plot(time_pts[:600], clean_eeg[:600], label="Clean Ground Truth EEG", color='black', linewidth=1.5)
    plt.plot(time_pts[:600], res_ccaf_eeg["e"][:600], label="CCAF Reconstructed EEG", color='blue', linestyle='--')
    plt.title("EEGdenoiseNet Ocular Artifact Cancellation (Scenario S7)")
    plt.xlabel("Sample Index")
    plt.ylabel("Normalized Signal")
    plt.legend(loc="upper right")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("results/s7_eeg_validation.png", dpi=250)
    plt.close()
    print("  [SAVED] results/s7_eeg_validation.png")

    print("\n" + "=" * 70)
    print("SCENARIO S7 VALIDATION COMPLETED SUCCESSFULLY")
    print("=" * 70)

if __name__ == "__main__":
    run_s7_biomedical_validation()
