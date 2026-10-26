import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from src.data.synthetic import generate_synthetic_data
from src.conformal.ccaf import CCAF, DecoupledACINLMS
from src.metrics.evaluator import compute_msd, compute_coverage, compute_winkler_score

def run_ablation_study():
    print("=" * 70)
    print("RUNNING PHASE 6: ABLATION STUDIES FOR CCAF")
    print("=" * 70)

    # 1. Sensitivity to ACI Adaptation Rate gamma
    gamma_values = [0.005, 0.01, 0.02, 0.05, 0.10]
    num_samples = 8000
    change_sample = 4000
    num_taps = 16

    data = generate_synthetic_data(
        scenario="S3",
        num_taps=num_taps,
        num_samples=num_samples,
        snr_db=20.0,
        step_change_sample=change_sample,
        seed=101
    )
    U = data["U"]
    d = data["d"]
    W_opt = data["W_opt"]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    print("\n[Ablation 1] Evaluating ACI Adaptation Rate gamma Sensitivity...")
    ax1 = axes[0]
    for g in gamma_values:
        filter_ccaf = CCAF(num_taps=num_taps, alpha=0.10, gamma=g, mu_min=0.05, mu_max=0.8)
        res = filter_ccaf.run(U, d)
        msd = compute_msd(res["W_history"], W_opt)
        cov = compute_coverage(d, res["y_lower"], res["y_upper"])
        wink = compute_winkler_score(d, res["y_lower"], res["y_upper"])
        print(f"  gamma = {g:<5} -> Coverage: {cov*100:.2f}% | Winkler: {wink:.3f}")
        ax1.plot(msd, label=f"$\\gamma={g}$", alpha=0.85)

    ax1.axvline(change_sample, color='red', linestyle='--', alpha=0.5, label="Plant Change")
    ax1.set_title("Sensitivity to ACI Rate $\\gamma$ (Scenario S3)")
    ax1.set_xlabel("Iteration (n)")
    ax1.set_ylabel("MSD (dB)")
    ax1.set_ylim(-35, 5)
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # 2. Sensitivity to Control Exponent p
    p_values = [0.5, 1.0, 1.5, 2.0]
    print("\n[Ablation 2] Evaluating Control Function Exponent p...")
    ax2 = axes[1]
    for p in p_values:
        filter_p = CCAF(num_taps=num_taps, alpha=0.10, gamma=0.02, mu_min=0.05, mu_max=0.8, p=p)
        res = filter_p.run(U, d)
        msd = compute_msd(res["W_history"], W_opt)
        cov = compute_coverage(d, res["y_lower"], res["y_upper"])
        wink = compute_winkler_score(d, res["y_lower"], res["y_upper"])
        print(f"  p = {p:<4} -> Coverage: {cov*100:.2f}% | Winkler: {wink:.3f}")
        ax2.plot(msd, label=f"$p={p}$", alpha=0.85)

    ax2.axvline(change_sample, color='red', linestyle='--', alpha=0.5, label="Plant Change")
    ax2.set_title("Sensitivity to Control Exponent $p$ (Scenario S3)")
    ax2.set_xlabel("Iteration (n)")
    ax2.set_ylabel("MSD (dB)")
    ax2.set_ylim(-35, 5)
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    plt.tight_layout()
    os.makedirs("results", exist_ok=True)
    out_path = os.path.join("results", "phase6_ablation_gamma_and_p.png")
    plt.savefig(out_path, dpi=250)
    plt.close()
    print(f"\n[SAVED] Ablation plot saved to {out_path}")

if __name__ == "__main__":
    run_ablation_study()
