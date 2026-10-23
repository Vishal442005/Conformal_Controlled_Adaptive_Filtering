import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from src.data.air_loader import generate_aec_simulation_data
from src.filters.baselines import (
    NLMSFilter,
    RLSFilter,
    KwongJohnstonVSSLMS,
    BenestyNPVSSNLMS,
    ConvexCombinationNLMS,
    KalmanOracleFilter
)
from src.conformal.ccaf import CCAF, DecoupledACINLMS
from src.metrics.evaluator import (
    compute_msd,
    compute_coverage,
    compute_winkler_score,
    compute_sliding_coverage
)

def run_air_aec_benchmark():
    print("=" * 75)
    print("RUNNING AACHEN IMPULSE RESPONSE (AIR) DATABASE BENCHMARK (AEC)")
    print("=" * 75)

    air_dir = os.path.abspath("data/air/AIR_1_4")
    # Path 1: Aula Carolina position 1
    air_file_1 = os.path.join(air_dir, "air_binaural_aula_carolina_0_1_1_90_3.mat")
    # Path 2: Aula Carolina position 2 (abrupt room acoustic path change)
    air_file_2 = os.path.join(air_dir, "air_binaural_aula_carolina_0_1_2_90_3.mat")

    num_taps = 64
    num_samples = 15000
    change_sample = 7500
    snr_db = 25.0
    seed = 42

    print(f"Loading true acoustic room impulse responses...")
    print(f"  Initial Path : {os.path.basename(air_file_1)}")
    print(f"  Changed Path : {os.path.basename(air_file_2)} (at sample n={change_sample})")

    data = generate_aec_simulation_data(
        air_path_initial=air_file_1,
        air_path_changed=air_file_2,
        num_samples=num_samples,
        num_taps=num_taps,
        snr_db=snr_db,
        change_sample=change_sample,
        seed=seed
    )

    U = data["U"]
    d = data["d"]
    W_opt = data["W_opt"]
    sigma_v = data["sigma_v"]

    # Filter suite
    filters = {
        "NLMS (fast mu=0.5)": NLMSFilter(num_taps=num_taps, mu=0.5),
        "NLMS (slow mu=0.05)": NLMSFilter(num_taps=num_taps, mu=0.05),
        "RLS (lambda=0.995)": RLSFilter(num_taps=num_taps, lmbda=0.995),
        "Kwong VSS-LMS": KwongJohnstonVSSLMS(num_taps=num_taps, alpha=0.97, gamma=0.005, mu_min=0.01, mu_max=0.5),
        "Benesty NP-VSS": BenestyNPVSSNLMS(num_taps=num_taps),
        "Convex Combination": ConvexCombinationNLMS(num_taps=num_taps, mu_fast=0.5, mu_slow=0.05),
        "Kalman Oracle": KalmanOracleFilter(num_taps=num_taps, sigma_v=sigma_v, sigma_q=0.0),
        "Decoupled ACI-NLMS": DecoupledACINLMS(num_taps=num_taps, mu_fixed=0.05, alpha=0.10, gamma=0.02),
        "Proposed CCAF": CCAF(num_taps=num_taps, alpha=0.10, gamma=0.02, mu_min=0.05, mu_max=0.7, p=1.0)
    }

    results = {}
    for name, f in filters.items():
        print(f"Executing {name} on AIR acoustic echo cancellation...")
        res = f.run(U, d)
        msd_db = compute_msd(res["W_history"], W_opt)
        results[name] = {
            "res": res,
            "msd_db": msd_db
        }

    ccaf_res = results["Proposed CCAF"]["res"]
    dec_res = results["Decoupled ACI-NLMS"]["res"]

    cov_ccaf = compute_coverage(d, ccaf_res["y_lower"], ccaf_res["y_upper"])
    cov_dec = compute_coverage(d, dec_res["y_lower"], dec_res["y_upper"])
    wink_ccaf = compute_winkler_score(d, ccaf_res["y_lower"], ccaf_res["y_upper"])
    wink_dec = compute_winkler_score(d, dec_res["y_lower"], dec_res["y_upper"])

    print("\n" + "=" * 75)
    print("AACHEN IMPULSE RESPONSE (AIR) BENCHMARK SUMMARY")
    print("=" * 75)
    print(f"Target Conformal Coverage  : 90.00%")
    print(f"Proposed CCAF Coverage     : {cov_ccaf*100:.2f}% | Winkler Score: {wink_ccaf:.3f}")
    print(f"Decoupled ACI Coverage     : {cov_dec*100:.2f}% | Winkler Score: {wink_dec:.3f}")
    print("-" * 75)
    for name in results:
        steady_msd = np.mean(results[name]["msd_db"][-1000:])
        print(f"{name:<25}: Steady-State MSD = {steady_msd:.2f} dB")
    print("=" * 75)

    # Plot results
    fig, axes = plt.subplots(3, 1, figsize=(11, 13), sharex=True)

    # 1. MSD Tracking
    ax = axes[0]
    for name, data_dict in results.items():
        style = '--' if 'Oracle' in name else ('-' if 'CCAF' in name else ':')
        width = 2.2 if 'CCAF' in name else 1.2
        ax.plot(data_dict["msd_db"], label=name, linestyle=style, linewidth=width)
    ax.axvline(change_sample, color='red', linestyle='--', alpha=0.7, label="Acoustic Path Change")
    ax.set_ylabel("MSD (dB)")
    ax.set_ylim(-35, 10)
    ax.set_title("Acoustic Echo Cancellation: Real Room Impulse Response Tracking (AIR Database)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right", fontsize=8, ncol=2)

    # 2. Step size and ACI control signal
    ax = axes[1]
    ax.plot(ccaf_res["mu_hist"], color='purple', label="CCAF Adaptive Step-Size $\\mu(n)$", linewidth=1.5)
    ax2 = ax.twinx()
    ax2.plot(ccaf_res["a_hist"], color='orange', linestyle='--', label="ACI State $\\alpha_n$", alpha=0.8)
    ax2.axhline(0.10, color='gray', linestyle=':', label="Target $\\alpha=0.10$")
    ax.axvline(change_sample, color='red', linestyle='--', alpha=0.7)
    ax.set_ylabel("Step Size $\\mu(n)$", color='purple')
    ax2.set_ylabel("ACI State $\\alpha_n$", color='orange')
    ax.set_title("CCAF Step-Size Control Reaction to Real Room Path Change")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left", fontsize=8)
    ax2.legend(loc="upper right", fontsize=8)

    # 3. Sliding Window Coverage
    ax = axes[2]
    slide_ccaf = compute_sliding_coverage(d, ccaf_res["y_lower"], ccaf_res["y_upper"], window=500)
    slide_dec = compute_sliding_coverage(d, dec_res["y_lower"], dec_res["y_upper"], window=500)
    ax.plot(np.arange(499, len(d)), slide_ccaf, label="CCAF Sliding Coverage", color='blue', linewidth=1.8)
    ax.plot(np.arange(499, len(d)), slide_dec, label="Decoupled ACI Sliding Coverage", color='gray', linestyle='--')
    ax.axhline(0.90, color='green', linestyle='-', label="Nominal 90% Coverage", linewidth=1.2)
    ax.axvline(change_sample, color='red', linestyle='--', alpha=0.7)
    ax.set_xlabel("Iteration (n)")
    ax.set_ylabel("Coverage Proportion")
    ax.set_ylim(0.70, 1.0)
    ax.set_title("Conformal Prediction Interval Coverage under Acoustic Room Dynamics")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower left", fontsize=8)

    plt.tight_layout()
    out_file = os.path.join("results", "air_database_aec_benchmark.png")
    plt.savefig(out_file, dpi=250)
    plt.close()
    print(f"\n[SAVED] Benchmark plot saved to: {out_file}")

if __name__ == "__main__":
    run_air_aec_benchmark()
