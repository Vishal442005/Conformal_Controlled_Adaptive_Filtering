import pytest
import numpy as np
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.filters.baselines import (
    LMSFilter,
    NLMSFilter,
    RLSFilter,
    KwongJohnstonVSSLMS,
    BenestyNPVSSNLMS,
    ConvexCombinationNLMS,
    KalmanOracleFilter
)

def test_lms_filter():
    filt = LMSFilter(num_taps=4, mu=0.01)
    u = np.array([1.0, 0.5, 0.2, 0.1])
    d = 2.0
    e = filt.update(u, d)
    assert isinstance(e, (float, np.floating))
    assert len(filt.w) == 4

def test_nlms_filter_stability():
    filt = NLMSFilter(num_taps=4, mu=0.1)
    u = np.random.randn(4) * 100 # high energy
    d = 1.0
    e = filt.update(u, d)
    assert not np.isnan(e)
    assert not np.isinf(filt.w).any()

def test_kwong_vss_step_clipping():
    filt = KwongJohnstonVSSLMS(num_taps=4, mu_min=0.01, mu_max=0.5)
    u = np.random.randn(4)
    filt.update(u, 1000.0) # massive error
    assert filt.mu <= filt.mu_max + 1e-6
    assert filt.mu >= filt.mu_min - 1e-6

def test_kalman_oracle():
    filt = KalmanOracleFilter(num_taps=4, sigma_v=0.1, sigma_q=0.0)
    u = np.ones(4)
    e = filt.update(u, 1.0)
    assert not np.isnan(e)
