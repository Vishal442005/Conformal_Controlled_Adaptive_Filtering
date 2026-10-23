import numpy as np

def compute_msd(W_history: np.ndarray, W_opt: np.ndarray) -> np.ndarray:
    """
    Compute Mean-Squared Deviation (MSD) in dB: 10 * log10( ||w_o(n) - w(n)||^2 )
    W_history: (N, M)
    W_opt: (N, M)
    """
    diff = W_history - W_opt
    msd_linear = np.sum(diff ** 2, axis=1)
    msd_db = 10.0 * np.log10(np.maximum(msd_linear, 1e-12))
    return msd_db

def compute_emse(e: np.ndarray, v: np.ndarray) -> np.ndarray:
    """
    Excess Mean Square Error (EMSE): e_a(n)^2 = (e(n) - v(n))^2
    """
    e_a = e - v
    return e_a ** 2

def compute_coverage(d: np.ndarray, y_lower: np.ndarray, y_upper: np.ndarray) -> float:
    """
    Empirical coverage: proportion of true observations d(n) within [y_lower, y_upper].
    """
    covered = (d >= y_lower) & (d <= y_upper)
    return float(np.mean(covered))

def compute_sliding_coverage(d: np.ndarray, y_lower: np.ndarray, y_upper: np.ndarray, window: int = 500) -> np.ndarray:
    """
    Sliding window empirical coverage.
    """
    covered = ((d >= y_lower) & (d <= y_upper)).astype(float)
    kernel = np.ones(window) / window
    return np.convolve(covered, kernel, mode='valid')

def compute_winkler_score(d: np.ndarray, y_lower: np.ndarray, y_upper: np.ndarray, alpha: float = 0.10) -> float:
    """
    Winkler Interval Score:
    Score = width + (2/alpha) * (y_lower - d) * I(d < y_lower) + (2/alpha) * (d - y_upper) * I(d > y_upper)
    """
    width = y_upper - y_lower
    penalty_below = (2.0 / alpha) * np.maximum(0.0, y_lower - d)
    penalty_above = (2.0 / alpha) * np.maximum(0.0, d - y_upper)
    score = width + penalty_below + penalty_above
    return float(np.mean(score))

def compute_detection_delay_and_recovery(msd_db: np.ndarray, change_point: int, threshold_db: float = -20.0):
    """
    Calculate number of iterations after change_point to reach within threshold_db.
    """
    post_change = msd_db[change_point:]
    recovered_indices = np.where(post_change <= threshold_db)[0]
    if len(recovered_indices) > 0:
        return int(recovered_indices[0])
    return len(post_change)
