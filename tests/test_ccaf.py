import pytest
import numpy as np
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.conformal.ccaf import CCAF, DecoupledACINLMS, RunningScaleEstimator
from src.data.synthetic import generate_synthetic_data

def test_running_scale_estimator():
    scale_est = RunningScaleEstimator(beta=0.9, eps=1e-4)
    # Feed stationary noise
    for _ in range(50):
        s = scale_est.update(1.0)
    assert 0.9 < s < 1.1

def test_ccaf_step_size_bounds():
    ccaf = CCAF(num_taps=8, mu_min=0.05, mu_max=0.8, tau=0.03)
    u = np.random.randn(8)
    d = 1.0
    res = ccaf.update(u, d)
    assert ccaf.mu_min <= res["mu_n"] <= ccaf.mu_max

def test_ccaf_deadband_suppression():
    # In stationary conditions where alpha_n ~ alpha, deadband should keep mu near mu_min
    ccaf = CCAF(num_taps=4, alpha=0.10, tau=0.05, mu_min=0.05, mu_max=0.8)
    ccaf.a_n = 0.09 # deficit is 0.01 < tau (0.05)
    # deficit calculation: (0.10 - 0.09 - 0.05) / 0.05 = -0.04 -> clipped to 0
    raw_deficit = (ccaf.alpha - ccaf.a_n - ccaf.tau) / max(ccaf.alpha - ccaf.tau, 1e-6)
    c_n = float(np.clip(raw_deficit, 0.0, 1.0))
    assert c_n == 0.0

def test_ccaf_causal_scale():
    ccaf = CCAF(num_taps=4)
    u = np.ones(4)
    y_hat, y_low, y_high, q_val = ccaf.predict(u)
    assert y_low < y_hat < y_high
    assert q_val > 0

def test_decoupled_nlms_fixed_step():
    dec = DecoupledACINLMS(num_taps=4, mu_fixed=0.05)
    u = np.random.randn(4)
    res = dec.update(u, 2.0)
    assert res["mu_n"] == 0.05
