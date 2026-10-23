import pytest
import numpy as np
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.metrics.evaluator import compute_msd, compute_coverage, compute_winkler_score
from src.metrics.stats_protocol import compute_cliffs_delta, paired_wilcoxon_test, holm_bonferroni_correction, clopper_pearson_coverage_ci

def test_coverage_metric():
    d = np.array([1.0, 2.0, 3.0, 4.0, 10.0])
    y_lower = np.array([0.5, 1.5, 2.5, 3.5, 5.0])
    y_upper = np.array([1.5, 2.5, 3.5, 4.5, 8.0])
    # 4 out of 5 covered
    cov = compute_coverage(d, y_lower, y_upper)
    assert cov == 0.8

def test_winkler_score():
    d = np.array([1.0, 2.0])
    y_lower = np.array([0.0, 0.0])
    y_upper = np.array([3.0, 1.5])
    # First is within [0, 3] -> width 3
    # Second is 2.0 > 1.5 -> width 1.5 + (2/0.1)*(0.5) = 1.5 + 10 = 11.5
    # Average = (3 + 11.5)/2 = 7.25
    score = compute_winkler_score(d, y_lower, y_upper, alpha=0.10)
    assert abs(score - 7.25) < 1e-4

def test_cliffs_delta():
    a = np.array([10, 11, 12])
    b = np.array([1, 2, 3])
    delta = compute_cliffs_delta(a, b)
    assert delta == 1.0

def test_clopper_pearson():
    low, high = clopper_pearson_coverage_ci(k_covered=90, n_total=100, alpha=0.05)
    assert 0.80 < low < 0.90
    assert 0.90 < high < 0.96
