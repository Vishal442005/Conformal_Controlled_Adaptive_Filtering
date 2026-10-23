import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json

from src.data.synthetic import generate_synthetic_data
from src.filters.baselines import (
    NLMSFilter,
    KwongJohnstonVSSLMS,
    BenestyNPVSSNLMS,
    ConvexCombinationNLMS
)
from src.conformal.ccaf import CCAF, DecoupledACINLMS
from src.metrics.evaluator import compute_coverage, compute_winkler_score, compute_msd

def run_comparative_study():
    print("=" * 80)
    print("RUNNING GENUINE COMPARATIVE STUDY ACROSS PARAMETER SWEEPS")
    print("=" * 80)

    num_taps = 16
    num_samples = 5000
    change_sample = 2500
    num_mc = 10  # 10 independent Monte Carlo seeds per parameter cell

    snr_levels = [5.0, 10.0, 15.0, 20.0, 25.0, 30.0]
    outlier_levels = [0.0, 0.02, 0.05, 0.10, 0.15]

    algorithms = [
        "NLMS (fast)",
        "NLMS (slow)",
        "Kwong VSS-LMS",
        "Benesty NP-VSS",
        "Convex Combination",
        "Decoupled ACI",
        "Proposed CCAF-DB"
    ]

    # Data structures for results across all algorithms
    emse_vs_snr = {alg: [] for alg in algorithms}
    delay_vs_snr = {alg: [] for alg in algorithms}
    winkler_vs_snr = {alg: [] for alg in algorithms}
    coverage_vs_snr = {alg: [] for alg in algorithms}

    print("\n--- 1. Sweeping Operating SNR Parameter [5 dB to 30 dB] ---")
    for snr in snr_levels:
        print(f"  Simulating SNR = {snr:.1f} dB (averaging {num_mc} paired MC trials)...")
        emse_cell = {alg: [] for alg in algorithms}
        delay_cell = {alg: [] for alg in algorithms}
        wink_cell = {alg: [] for alg in algorithms}
        cov_cell = {alg: [] for alg in algorithms}

        for seed_idx in range(num_mc):
            seed = 9000 + int(snr * 10) + seed_idx
            data = generate_synthetic_data(
                scenario="S3",
                num_taps=num_taps,
                num_samples=num_samples,
                snr_db=snr,
                step_change_sample=change_sample,
                seed=seed
            )
            U = data["U"]
            d = data["d"]
            W_opt = data["W_opt"]
            v = data["v"]

            filters = {
                "NLMS (fast)": NLMSFilter(num_taps=num_taps, mu=0.5),
                "NLMS (slow)": NLMSFilter(num_taps=num_taps, mu=0.05),
                "Kwong VSS-LMS": KwongJohnstonVSSLMS(num_taps=num_taps, alpha=0.97, gamma=0.005, mu_min=0.01, mu_max=0.5),
                "Benesty NP-VSS": BenestyNPVSSNLMS(num_taps=num_taps),
                "Convex Combination": ConvexCombinationNLMS(num_taps=num_taps, mu_fast=0.5, mu_slow=0.05),
                "Decoupled ACI": DecoupledACINLMS(num_taps=num_taps, mu_fixed=0.05, alpha=0.10, gamma=0.02),
                "Proposed CCAF-DB": CCAF(num_taps=num_taps, alpha=0.10, gamma=0.02, mu_min=0.05, mu_max=0.8, tau=0.03)
            }

            for name, f in filters.items():
                res = f.run(U, d)
                # Steady-state excess MSE over final 400 samples
                ea = res["e"][-400:] - v[-400:]
                emse_lin = float(np.mean(ea ** 2))
                emse_cell[name].append(10.0 * np.log10(max(emse_lin, 1e-12)))

                # Recovery delay: samples to recover to within -18 dB MSD
                diff = res["W_history"] - W_opt
                msd_db = 10.0 * np.log10(np.maximum(np.sum(diff ** 2, axis=1), 1e-12))
                rec = np.where(msd_db[change_sample:] <= -18.0)[0]
                delay = int(rec[0]) if len(rec) > 0 else (num_samples - change_sample)
                delay_cell[name].append(delay)

                # Uncertainty Quantification:
                # If conformal filter, use its adaptive prediction interval.
                # If classical point estimator baseline, construct standard Gaussian 90% confidence interval:
                # y_hat +- 1.645 * running_rms(e)
                if "y_lower" in res:
                    yl = res["y_lower"]
                    yu = res["y_upper"]
                else:
                    e_arr = res["e"]
                    var_est = 1.0
                    s_arr = np.zeros(len(e_arr))
                    for i in range(len(e_arr)):
                        var_est = 0.95 * var_est + 0.05 * (e_arr[i] ** 2)
                        s_arr[i] = np.sqrt(var_est)
                    yl = res["y_hat"] - 1.645 * s_arr
                    yu = res["y_hat"] + 1.645 * s_arr

                cov = compute_coverage(d, yl, yu)
                wink = compute_winkler_score(d, yl, yu)
                cov_cell[name].append(cov)
                wink_cell[name].append(wink)

        for alg in algorithms:
            emse_vs_snr[alg].append(float(np.mean(emse_cell[alg])))
            delay_vs_snr[alg].append(float(np.mean(delay_cell[alg])))
            winkler_vs_snr[alg].append(float(np.mean(wink_cell[alg])))
            coverage_vs_snr[alg].append(float(np.mean(cov_cell[alg])))

    print("\n--- 2. Sweeping Outlier Probability Parameter [0% to 15%] ---")
    emse_vs_outlier = {alg: [] for alg in algorithms}
    for prob in outlier_levels:
        print(f"  Simulating Outlier Ratio = {prob*100:.0f}%...")
        emse_out_cell = {alg: [] for alg in algorithms}
        for seed_idx in range(num_mc):
            seed = 9500 + int(prob * 100) + seed_idx
            data = generate_synthetic_data(
                scenario="S6",
                num_taps=num_taps,
                num_samples=num_samples,
                snr_db=20.0,
                outlier_prob=prob,
                outlier_scale=10.0,
                seed=seed
            )
            U = data["U"]
            d = data["d"]
            v = data["v"]

            filters = {
                "NLMS (fast)": NLMSFilter(num_taps=num_taps, mu=0.5),
                "NLMS (slow)": NLMSFilter(num_taps=num_taps, mu=0.05),
                "Kwong VSS-LMS": KwongJohnstonVSSLMS(num_taps=num_taps, alpha=0.97, gamma=0.005, mu_min=0.01, mu_max=0.5),
                "Benesty NP-VSS": BenestyNPVSSNLMS(num_taps=num_taps),
                "Convex Combination": ConvexCombinationNLMS(num_taps=num_taps, mu_fast=0.5, mu_slow=0.05),
                "Decoupled ACI": DecoupledACINLMS(num_taps=num_taps, mu_fixed=0.05, alpha=0.10, gamma=0.02),
                "Proposed CCAF-DB": CCAF(num_taps=num_taps, alpha=0.10, gamma=0.02, mu_min=0.05, mu_max=0.8, tau=0.03)
            }

            for name, f in filters.items():
                res = f.run(U, d)
                ea = res["e"][-400:] - v[-400:]
                emse_lin = float(np.mean(ea ** 2))
                emse_out_cell[name].append(10.0 * np.log10(max(emse_lin, 1e-12)))

        for alg in algorithms:
            emse_vs_outlier[alg].append(float(np.mean(emse_out_cell[alg])))

    # -------------------------------------------------------------
    # 3. Generate Genuine 4-Panel Publication Comparison Plot
    # -------------------------------------------------------------
    print("\nGenerating Genuine 4-Panel Comparative Benchmark Plot...")
    fig, axes = plt.subplots(2, 2, figsize=(13, 10))
    colors = {
        "NLMS (fast)": "#E74C3C",
        "NLMS (slow)": "#34495E",
        "Kwong VSS-LMS": "#F39C12",
        "Benesty NP-VSS": "#9B59B6",
        "Convex Combination": "#1ABC9C",
        "Decoupled ACI": "#3498DB",
        "Proposed CCAF-DB": "#27AE60"
    }
    markers = {
        "NLMS (fast)": "o",
        "NLMS (slow)": "s",
        "Kwong VSS-LMS": "^",
        "Benesty NP-VSS": "d",
        "Convex Combination": "v",
        "Decoupled ACI": "x",
        "Proposed CCAF-DB": "D"
    }

    # Panel (a): Steady-state EMSE vs Operating SNR
    ax = axes[0, 0]
    for alg in algorithms:
        lw = 2.5 if "CCAF" in alg else 1.4
        ax.plot(snr_levels, emse_vs_snr[alg], label=alg, color=colors[alg], marker=markers[alg], linewidth=lw, markersize=6)
    ax.set_title("(a) Steady-State EMSE vs. Operating SNR", fontsize=11, fontweight='bold')
    ax.set_xlabel("Signal-to-Noise Ratio (SNR in dB)", fontsize=10)
    ax.set_ylabel("Steady-State EMSE (dB)", fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(fontsize=8, loc='lower left')

    # Panel (b): Recovery Delay after Abrupt Disruption vs SNR
    ax = axes[0, 1]
    for alg in algorithms:
        lw = 2.5 if "CCAF" in alg else 1.4
        ax.plot(snr_levels, delay_vs_snr[alg], label=alg, color=colors[alg], marker=markers[alg], linewidth=lw, markersize=6)
    ax.set_title("(b) Tracking Recovery Delay vs. Operating SNR", fontsize=11, fontweight='bold')
    ax.set_xlabel("Signal-to-Noise Ratio (SNR in dB)", fontsize=10)
    ax.set_ylabel("Recovery Delay (Samples to reach -18 dB)", fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(fontsize=8, loc='upper right')

    # Panel (c): Sensitivity to Impulsive Outlier Contamination Rate
    ax = axes[1, 0]
    for alg in algorithms:
        lw = 2.5 if "CCAF" in alg else 1.4
        ax.plot([p * 100 for p in outlier_levels], emse_vs_outlier[alg], label=alg, color=colors[alg], marker=markers[alg], linewidth=lw, markersize=6)
    ax.set_title("(c) Robustness to Impulsive Outlier Probability", fontsize=11, fontweight='bold')
    ax.set_xlabel("Outlier Contamination Probability (%)", fontsize=10)
    ax.set_ylabel("Excess MSE under Outliers (dB)", fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(fontsize=8, loc='lower right')

    # Panel (d): Winkler Interval Score across Operating SNRs (All Algorithms)
    ax = axes[1, 1]
    for alg in algorithms:
        lw = 2.5 if "CCAF" in alg else 1.4
        ax.plot(snr_levels, winkler_vs_snr[alg], label=alg, color=colors[alg], marker=markers[alg], linewidth=lw, markersize=6)
    ax.set_title("(d) Prediction Interval Sharpness (Winkler Score across All Algorithms)", fontsize=11, fontweight='bold')
    ax.set_xlabel("Signal-to-Noise Ratio (SNR in dB)", fontsize=10)
    ax.set_ylabel("Winkler Score (Lower is Sharper)", fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(fontsize=8, loc='upper right')

    plt.tight_layout()
    plot_file = os.path.abspath("results/comparative_study_benchmark.png")
    plt.savefig(plot_file, dpi=300)
    plt.close()
    print(f"[SAVED] Comparative study figure saved to: {plot_file}")

    # -------------------------------------------------------------
    # 4. Save Numerical Results to JSON for Direct Table Injection
    # -------------------------------------------------------------
    results_payload = {
        "parameters": {
            "snr_levels_db": snr_levels,
            "outlier_levels_pct": [p * 100 for p in outlier_levels]
        },
        "emse_vs_snr": emse_vs_snr,
        "delay_vs_snr": delay_vs_snr,
        "emse_vs_outlier": emse_vs_outlier,
        "winkler_vs_snr": winkler_vs_snr,
        "coverage_vs_snr": coverage_vs_snr
    }

    json_file = os.path.abspath("results/comparative_study_results.json")
    with open(json_file, "w") as f:
        json.dump(results_payload, f, indent=2)
    print(f"[SAVED] Genuine comparative results saved to: {json_file}")

if __name__ == "__main__":
    run_comparative_study()
