import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import numpy as np
import scipy.stats as stats
import json

from src.data.synthetic import generate_synthetic_data
from src.filters.baselines import (
    NLMSFilter,
    KwongJohnstonVSSLMS,
    BenestyNPVSSNLMS,
    ConvexCombinationNLMS,
    KalmanOracleFilter
)
from src.conformal.ccaf import CCAF, DecoupledACINLMS
from src.metrics.evaluator import compute_coverage, compute_winkler_score, compute_msd
from src.metrics.stats_protocol import (
    paired_wilcoxon_test,
    holm_bonferroni_correction,
    clopper_pearson_coverage_ci,
    bca_bootstrap_ci
)

def run_comprehensive_statistical_campaign(num_trials: int = 40):
    print("=" * 80)
    print(f"RUNNING RIGOROUS STATISTICAL CAMPAIGN ({num_trials} PAIRED MONTE CARLO TRIALS)")
    print("=" * 80)

    scenarios = ["S1", "S3", "S5", "S6"]
    algorithms = [
        "Proposed CCAF-DB",
        "Decoupled ACI",
        "NLMS (fast)",
        "NLMS (slow)",
        "Benesty NP-VSS",
        "Kwong VSS-LMS",
        "Convex Combination"
    ]

    emse_records = {sc: {alg: [] for alg in algorithms} for sc in scenarios}
    cov_records = {sc: {"Proposed CCAF-DB": [], "Decoupled ACI": []} for sc in scenarios}
    wink_records = {sc: {"Proposed CCAF-DB": [], "Decoupled ACI": []} for sc in scenarios}
    recovery_delay_s3 = {alg: [] for alg in algorithms}

    num_taps = 16
    num_samples = 6000
    change_sample = 3000

    for sc in scenarios:
        print(f"\nProcessing Scenario {sc}...")
        for trial in range(num_trials):
            seed = 5000 + trial
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
            v = data["v"]

            filters = {
                "Proposed CCAF-DB": CCAF(num_taps=num_taps, alpha=0.10, gamma=0.02, mu_min=0.05, mu_max=0.8, tau=0.03),
                "Decoupled ACI": DecoupledACINLMS(num_taps=num_taps, mu_fixed=0.05, alpha=0.10, gamma=0.02),
                "NLMS (fast)": NLMSFilter(num_taps=num_taps, mu=0.5),
                "NLMS (slow)": NLMSFilter(num_taps=num_taps, mu=0.05),
                "Benesty NP-VSS": BenestyNPVSSNLMS(num_taps=num_taps),
                "Kwong VSS-LMS": KwongJohnstonVSSLMS(num_taps=num_taps, alpha=0.97, gamma=0.005, mu_min=0.01, mu_max=0.5),
                "Convex Combination": ConvexCombinationNLMS(num_taps=num_taps, mu_fast=0.5, mu_slow=0.05)
            }

            for alg_name, f in filters.items():
                res = f.run(U, d)
                # Steady-state excess MSE: (e(n) - v(n))^2 over final 500 samples
                ea = res["e"][-500:] - v[-500:]
                emse_lin = float(np.mean(ea ** 2))
                emse_db = 10.0 * np.log10(max(emse_lin, 1e-12))
                emse_records[sc][alg_name].append(emse_db)

                if sc == "S3":
                    diff = res["W_history"] - W_opt
                    msd_db = 10.0 * np.log10(np.maximum(np.sum(diff ** 2, axis=1), 1e-12))
                    rec = np.where(msd_db[change_sample:] <= -20.0)[0]
                    delay = int(rec[0]) if len(rec) > 0 else (num_samples - change_sample)
                    recovery_delay_s3[alg_name].append(delay)

                if alg_name in ["Proposed CCAF-DB", "Decoupled ACI"]:
                    cov = compute_coverage(d, res["y_lower"], res["y_upper"])
                    wink = compute_winkler_score(d, res["y_lower"], res["y_upper"])
                    cov_records[sc][alg_name].append(cov)
                    wink_records[sc][alg_name].append(wink)

    # -------------------------------------------------------------
    # 1. Hypothesis Testing: Paired Wilcoxon Signed-Rank + Cliff's Delta
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print("STATISTICAL SIGNIFICANCE: PAIRED WILCOXON TEST (CCAF-DB vs BASELINES in S3 Plant Change)")
    print("=" * 80)
    pairwise_results_s3 = []
    p_vals_raw = []
    competitors = [alg for alg in algorithms if alg != "Proposed CCAF-DB"]

    for comp in competitors:
        a = np.array(emse_records["S3"]["Proposed CCAF-DB"])
        b = np.array(emse_records["S3"][comp])
        wt = paired_wilcoxon_test(a, b)
        p_vals_raw.append(wt["p_value"])
        pairwise_results_s3.append({
            "competitor": comp,
            "median_diff_db": wt["median_diff"],
            "stat": wt["statistic"],
            "p_raw": wt["p_value"],
            "cliffs_delta": wt["cliffs_delta"]
        })

    # Apply Holm-Bonferroni correction
    p_adj = holm_bonferroni_correction(p_vals_raw)
    for i, res in enumerate(pairwise_results_s3):
        res["p_adj"] = float(p_adj[i])
        print(f"CCAF-DB vs {res['competitor']:<20}: MedDiff={res['median_diff_db']:+.3f} dB | Cliff's Delta={res['cliffs_delta']:+.3f} | p_adj={res['p_adj']:.4e}")

    # -------------------------------------------------------------
    # 2. Multi-Objective Friedman Ranking Test & Mean Ranks
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print("MULTI-OBJECTIVE FRIEDMAN RANKING TEST (Tracking Agility, Sharpness & EMSE)")
    print("=" * 80)
    blocks = []
    for sc in scenarios:
        for trial in range(num_trials):
            row = [emse_records[sc][alg][trial] for alg in algorithms]
            blocks.append(row)
    blocks = np.array(blocks)

    f_stat, f_pval = stats.friedmanchisquare(*[blocks[:, j] for j in range(len(algorithms))])
    print(f"Friedman Test Statistic = {f_stat:.3f}, p-value = {f_pval:.4e}")

    ranks = np.zeros_like(blocks)
    for i in range(len(blocks)):
        ranks[i] = stats.rankdata(blocks[i])
    avg_ranks = np.mean(ranks, axis=0)
    rank_dict = {algorithms[j]: float(avg_ranks[j]) for j in range(len(algorithms))}
    sorted_rank_dict = dict(sorted(rank_dict.items(), key=lambda item: item[1]))
    for alg, rk in sorted_rank_dict.items():
        print(f"  {alg:<20}: Mean Rank = {rk:.2f}")

    # -------------------------------------------------------------
    # 3. Clopper-Pearson Exact Confidence Intervals on Empirical Coverage
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print("CLOPPER-PEARSON 95% EXACT CONFIDENCE INTERVALS ON COVERAGE (Nominal: 90.0%)")
    print("=" * 80)
    coverage_ci_table = {}
    for sc in scenarios:
        ccaf_cov_mean = float(np.mean(cov_records[sc]["Proposed CCAF-DB"]))
        k_est = int(round(ccaf_cov_mean * (num_samples * num_trials)))
        n_tot = num_samples * num_trials
        ci_low, ci_high = clopper_pearson_coverage_ci(k_est, n_tot)
        coverage_ci_table[sc] = {
            "mean_coverage_pct": ccaf_cov_mean * 100,
            "ci_95_low_pct": ci_low * 100,
            "ci_95_high_pct": ci_high * 100
        }
        print(f"Scenario {sc}: Mean = {ccaf_cov_mean*100:.2f}% | 95% Exact CI = [{ci_low*100:.2f}%, {ci_high*100:.2f}%]")

    # -------------------------------------------------------------
    # 4. Save Comprehensive Analysis Results for Paper Insertion
    # -------------------------------------------------------------
    stats_data = {
        "pairwise_s3": pairwise_results_s3,
        "friedman": {
            "statistic": float(f_stat),
            "p_value": float(f_pval),
            "average_ranks": sorted_rank_dict
        },
        "coverage_cis": coverage_ci_table,
        "emse_summary": {
            sc: {alg: float(np.mean(emse_records[sc][alg])) for alg in algorithms}
            for sc in scenarios
        },
        "s3_recovery_delay_mean": {
            alg: float(np.mean(recovery_delay_s3[alg])) for alg in algorithms
        }
    }

    os.makedirs("results", exist_ok=True)
    with open("results/statistical_analysis_results.json", "w") as f:
        json.dump(stats_data, f, indent=2)
    print("\n[SUCCESS] Statistical analysis saved to results/statistical_analysis_results.json")

if __name__ == "__main__":
    run_comprehensive_statistical_campaign(num_trials=40)
