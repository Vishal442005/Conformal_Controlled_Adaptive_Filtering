import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import scipy.stats as stats

def compute_cliffs_delta(a: np.ndarray, b: np.ndarray) -> float:
    """
    Computes exact Cliff's delta effect size between two distributions:
      delta = (sum_{i,j} sign(a_i - b_j)) / (n_a * n_b)
    Interpretation:
      |delta| < 0.147: negligible
      0.147 <= |delta| < 0.33: small
      0.33 <= |delta| < 0.474: medium
      |delta| >= 0.474: large
    """
    diff_matrix = np.subtract.outer(a, b)
    greater = np.sum(diff_matrix > 0)
    lesser = np.sum(diff_matrix < 0)
    return float((greater - lesser) / (len(a) * len(b)))

def paired_wilcoxon_test(emse_a: np.ndarray, emse_b: np.ndarray):
    """
    Paired Wilcoxon signed-rank test on per-run steady-state EMSE.
    Returns: stat, p_value, cliffs_delta, median_diff
    """
    diff = emse_a - emse_b
    res = stats.wilcoxon(emse_a, emse_b, zero_method="wilcox", correction=True)
    cliffs_delta = compute_cliffs_delta(emse_a, emse_b)

    return {
        "statistic": float(res.statistic),
        "p_value": float(res.pvalue),
        "cliffs_delta": cliffs_delta,
        "median_diff": float(np.median(diff))
    }

def holm_bonferroni_correction(p_values: list):
    """
    Holm-Bonferroni step-down correction for multiple pairwise comparisons.
    """
    m = len(p_values)
    sorted_indices = np.argsort(p_values)
    adjusted_p = np.zeros(m)
    
    running_max = 0.0
    for rank, idx in enumerate(sorted_indices):
        p = p_values[idx]
        adj = p * (m - rank)
        running_max = max(running_max, adj)
        adjusted_p[idx] = min(running_max, 1.0)
        
    return adjusted_p

def clopper_pearson_coverage_ci(k_covered: int, n_total: int, alpha: float = 0.05):
    """
    Clopper-Pearson exact binomial confidence interval for empirical coverage.
    """
    if k_covered == 0:
        low = 0.0
    else:
        low = stats.beta.ppf(alpha / 2, k_covered, n_total - k_covered + 1)
        
    if k_covered == n_total:
        high = 1.0
    else:
        high = stats.beta.ppf(1 - alpha / 2, k_covered + 1, n_total - k_covered)
        
    return float(low), float(high)

def bca_bootstrap_ci(data: np.ndarray, num_resamples: int = 2000, alpha: float = 0.05):
    """
    Bootstrap mean confidence interval.
    """
    n = len(data)
    boot_means = np.zeros(num_resamples)
    rng = np.random.default_rng(123)
    for i in range(num_resamples):
        sample = rng.choice(data, size=n, replace=True)
        boot_means[i] = np.mean(sample)
    low = np.percentile(boot_means, 100 * (alpha / 2))
    high = np.percentile(boot_means, 100 * (1 - alpha / 2))
    return float(low), float(high)
