import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from src.data.synthetic import generate_synthetic_data
from src.filters.baselines import (
    NLMSFilter,
    RLSFilter,
    KwongJohnstonVSSLMS,
    BenestyNPVSSNLMS,
    ConvexCombinationNLMS,
    KalmanOracleFilter
)
from src.conformal.ccaf import CCAF, DecoupledACINLMS
from src.metrics.evaluator import compute_msd, compute_coverage, compute_winkler_score, compute_sliding_coverage

def run_scenario_s3_demo():
    print("=" * 60)
    print("Running Scenario S3 Benchmark (Abrupt Plant Change at n=4000)...")
    print("=" * 60)

    num_taps = 16
    num_samples = 10000
    change_sample = 4000
    snr_db = 20.0
    seed = 42

    data = generate_synthetic_data(
        scenario="S3",
        num_taps=num_taps,
        num_samples=num_samples,
        snr_db=snr_db,
        step_change_sample=change_sample,
        seed=seed
    )
    U = data["U"]
    d = data["d"]
    W_opt = data["W_opt"]
    sigma_v = data["sigma_v"]

    # Initialize Filters
    filters = {
        "NLMS (fast, mu=0.5)": NLMSFilter(num_taps=num_taps, mu=0.5),
        "NLMS (slow, mu=0.05)": NLMSFilter(num_taps=num_taps, mu=0.05),
        "RLS (lambda=0.99)": RLSFilter(num_taps=num_taps, lmbda=0.99),
        "Kwong VSS-LMS": KwongJohnstonVSSLMS(num_taps=num_taps, alpha=0.97, gamma=0.005, mu_min=0.001, mu_max=0.5),
        "Benesty NP-VSS-NLMS": BenestyNPVSSNLMS(num_taps=num_taps),
        "Convex Combination": ConvexCombinationNLMS(num_taps=num_taps, mu_fast=0.5, mu_slow=0.05),
        "Kalman Oracle": KalmanOracleFilter(num_taps=num_taps, sigma_v=sigma_v, sigma_q=0.0),
        "Decoupled ACI-NLMS": DecoupledACINLMS(num_taps=num_taps, mu_fixed=0.05, alpha=0.10, gamma=0.02),
        "Proposed CCAF": CCAF(num_taps=num_taps, alpha=0.10, gamma=0.02, mu_min=0.05, mu_max=0.8, p=1.0)
    }

    results = {}
    for name, f in filters.items():
        print(f"Executing {name}...")
        res = f.run(U, d)
        msd_db = compute_msd(res["W_history"], W_opt)
        results[name] = {
            "res": res,
            "msd_db": msd_db
        }

    # Evaluate Coverage & Winkler Scores for interval methods
    ccaf_res = results["Proposed CCAF"]["res"]
    decoupled_res = results["Decoupled ACI-NLMS"]["res"]

    cov_ccaf = compute_coverage(d, ccaf_res["y_lower"], ccaf_res["y_upper"])
    cov_decoupled = compute_coverage(d, decoupled_res["y_lower"], decoupled_res["y_upper"])

    wink_ccaf = compute_winkler_score(d, ccaf_res["y_lower"], ccaf_res["y_upper"])
    wink_decoupled = compute_winkler_score(d, decoupled_res["y_lower"], decoupled_res["y_upper"])

    print("\n--- Uncertainty Quantification Summary (Target Coverage: 90.0%) ---")
    print(f"Proposed CCAF       -> Empirical Coverage: {cov_ccaf*100:.2f}% | Winkler Score: {wink_ccaf:.3f}")
    print(f"Decoupled ACI-NLMS  -> Empirical Coverage: {cov_decoupled*100:.2f}% | Winkler Score: {wink_decoupled:.3f}")

    # Plot results
    os.makedirs("results", exist_ok=True)
    fig, axes = plt.subplots(3, 1, figsize=(11, 13), sharex=True)

    # 1. MSD Comparison
    ax = axes[0]
    for name, data_dict in results.items():
        style = '--' if 'Oracle' in name else ('-' if 'CCAF' in name else ':')
        width = 2.5 if 'CCAF' in name else 1.2
        ax.plot(data_dict["msd_db"], label=name, linestyle=style, linewidth=width)
    ax.axvline(change_sample, color='red', linestyle='--', alpha=0.6, label='Abrupt Change (n=4000)')
    ax.set_ylabel("MSD (dB)")
    ax.set_ylim(-35, 10)
    ax.set_title("Tracking Performance: Mean-Squared Deviation (MSD in dB)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right", fontsize=8, ncol=2)

    # 2. CCAF Adaptive Step-Size & ACI State
    ax = axes[1]
    ax.plot(ccaf_res["mu_hist"], color='purple', label="CCAF Adaptive Step-Size $\\mu(n)$", linewidth=1.5)
    ax2 = ax.twinx()
    ax2.plot(ccaf_res["a_hist"], color='orange', linestyle='--', label="ACI State $\\alpha_n$", alpha=0.8)
    ax2.axhline(0.10, color='gray', linestyle=':', label="Target $\\alpha=0.10$")
    ax.axvline(change_sample, color='red', linestyle='--', alpha=0.6)
    ax.set_ylabel("Step Size $\\mu(n)$", color='purple')
    ax2.set_ylabel("ACI State $\\alpha_n$", color='orange')
    ax.set_title("CCAF Internal Control Dynamics: Coverage Error Drives Step-Size Boost")
    ax.grid(True, alpha=0.3)

    # 3. Sliding Window Coverage (Window = 400)
    ax = axes[2]
    slide_ccaf = compute_sliding_coverage(d, ccaf_res["y_lower"], ccaf_res["y_upper"], window=400)
    slide_dec = compute_sliding_coverage(d, decoupled_res["y_lower"], decoupled_res["y_upper"], window=400)
    ax.plot(np.arange(400-1, len(d)), slide_ccaf, label="CCAF Sliding Coverage", color='blue', linewidth=1.8)
    ax.plot(np.arange(400-1, len(d)), slide_dec, label="Decoupled ACI Sliding Coverage", color='gray', linestyle='--')
    ax.axhline(0.90, color='green', linestyle='-', label="Nominal Coverage (90%)", linewidth=1.2)
    ax.axvline(change_sample, color='red', linestyle='--', alpha=0.6)
    ax.set_xlabel("Iteration (n)")
    ax.set_ylabel("Coverage Proportion")
    ax.set_ylim(0.70, 1.0)
    ax.set_title("Empirical Coverage Guarantee (Window = 400)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower left", fontsize=8)

    plt.tight_layout()
    output_path = os.path.join("results", "s3_benchmark_comparison.png")
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"\n[SUCCESS] Generated benchmark comparison plot: {output_path}")

if __name__ == "__main__":
    run_scenario_s3_demo()
