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
from src.metrics.evaluator import (
    compute_msd,
    compute_coverage,
    compute_winkler_score,
    compute_detection_delay_and_recovery
)

def run_monte_carlo_campaign(num_monte_carlo: int = 50):
    """
    Runs multi-run Monte Carlo experiments across scenarios S1, S3, S5, S6
    """
    print(f"Starting Monte Carlo Evaluation Suite ({num_monte_carlo} independent paired runs)...")
    scenarios = ["S1", "S3", "S5", "S6"]
    num_taps = 16
    num_samples = 8000
    change_sample = 4000

    summary_records = []

    for sc in scenarios:
        print(f"\n---> Evaluating Scenario {sc}...")
        msd_accum = {
            "CCAF": np.zeros(num_samples),
            "Decoupled ACI": np.zeros(num_samples),
            "NLMS (fast)": np.zeros(num_samples),
            "NLMS (slow)": np.zeros(num_samples),
            "Benesty NP-VSS": np.zeros(num_samples),
            "Kwong VSS-LMS": np.zeros(num_samples),
            "Convex Combination": np.zeros(num_samples),
            "Kalman Oracle": np.zeros(num_samples)
        }
        cov_list_ccaf = []
        cov_list_dec = []
        wink_list_ccaf = []
        wink_list_dec = []

        for trial in range(num_monte_carlo):
            seed = 1000 + trial
            data = generate_synthetic_data(
                scenario=sc,
                num_taps=num_taps,
                num_samples=num_samples,
                snr_db=20.0,
                step_change_sample=change_sample,
                seed=seed
            )
            U = data["U"]
            d = data["d"]
            W_opt = data["W_opt"]
            sigma_v = data["sigma_v"]

            filters = {
                "NLMS (fast)": NLMSFilter(num_taps=num_taps, mu=0.5),
                "NLMS (slow)": NLMSFilter(num_taps=num_taps, mu=0.05),
                "Kwong VSS-LMS": KwongJohnstonVSSLMS(num_taps=num_taps, alpha=0.97, gamma=0.005, mu_min=0.001, mu_max=0.5),
                "Benesty NP-VSS": BenestyNPVSSNLMS(num_taps=num_taps),
                "Convex Combination": ConvexCombinationNLMS(num_taps=num_taps, mu_fast=0.5, mu_slow=0.05),
                "Kalman Oracle": KalmanOracleFilter(num_taps=num_taps, sigma_v=sigma_v, sigma_q=0.0),
                "Decoupled ACI": DecoupledACINLMS(num_taps=num_taps, mu_fixed=0.05, alpha=0.10, gamma=0.02),
                "CCAF": CCAF(num_taps=num_taps, alpha=0.10, gamma=0.02, mu_min=0.05, mu_max=0.8, p=1.0)
            }

            for name, f in filters.items():
                res = f.run(U, d)
                diff = res["W_history"] - W_opt
                msd_lin = np.sum(diff ** 2, axis=1)
                msd_accum[name] += msd_lin

                if name == "CCAF":
                    cov_list_ccaf.append(compute_coverage(d, res["y_lower"], res["y_upper"]))
                    wink_list_ccaf.append(compute_winkler_score(d, res["y_lower"], res["y_upper"]))
                elif name == "Decoupled ACI":
                    cov_list_dec.append(compute_coverage(d, res["y_lower"], res["y_upper"]))
                    wink_list_dec.append(compute_winkler_score(d, res["y_lower"], res["y_upper"]))

        # Average MSD in dB
        plt.figure(figsize=(9, 5))
        for name in msd_accum:
            avg_lin = msd_accum[name] / num_monte_carlo
            msd_db = 10.0 * np.log10(np.maximum(avg_lin, 1e-12))
            lw = 2.2 if name == "CCAF" else (1.5 if "Oracle" in name else 1.0)
            ls = '-' if name == "CCAF" else ('--' if "Oracle" in name else ':')
            plt.plot(msd_db, label=name, linewidth=lw, linestyle=ls)

        if sc == "S3":
            plt.axvline(change_sample, color='red', linestyle='--', alpha=0.5, label="Plant Change")

        plt.title(f"Scenario {sc} - Monte Carlo MSD Learning Curve (N={num_monte_carlo} runs)")
        plt.xlabel("Iteration (n)")
        plt.ylabel("MSD (dB)")
        plt.grid(True, alpha=0.3)
        plt.legend(fontsize=8, loc="upper right")
        plt.tight_layout()
        plt.savefig(f"results/monte_carlo_{sc}.png", dpi=200)
        plt.close()

        record = {
            "Scenario": sc,
            "CCAF_Coverage": np.mean(cov_list_ccaf) * 100,
            "Decoupled_Coverage": np.mean(cov_list_dec) * 100,
            "CCAF_Winkler": np.mean(wink_list_ccaf),
            "Decoupled_Winkler": np.mean(wink_list_dec),
            "SteadyState_MSD_dB_CCAF": 10.0 * np.log10(np.mean((msd_accum["CCAF"] / num_monte_carlo)[-500:])),
            "SteadyState_MSD_dB_Oracle": 10.0 * np.log10(np.mean((msd_accum["Kalman Oracle"] / num_monte_carlo)[-500:])),
        }
        summary_records.append(record)

    print("\n" + "="*80)
    print("MONTE CARLO STATISTICAL SUMMARY TABLE")
    print("="*80)
    header = f"{'Scenario':<10} | {'CCAF Cov (%)':<14} | {'Dec Cov (%)':<14} | {'CCAF Winkler':<14} | {'Dec Winkler':<14} | {'CCAF MSD (dB)':<14}"
    print(header)
    print("-" * len(header))
    for r in summary_records:
        row = f"{r['Scenario']:<10} | {r['CCAF_Coverage']:<14.2f} | {r['Decoupled_Coverage']:<14.2f} | {r['CCAF_Winkler']:<14.3f} | {r['Decoupled_Winkler']:<14.3f} | {r['SteadyState_MSD_dB_CCAF']:<14.2f}"
        print(row)
    print("="*80)
    print("All figures saved to results/ directory.")

if __name__ == "__main__":
    run_monte_carlo_campaign(num_monte_carlo=30)
