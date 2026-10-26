import numpy as np
from collections import deque

class RunningScaleEstimator:
    """
    Tracks running error scale s(n) via exponentially weighted RMS of past errors.
    """
    def __init__(self, beta: float = 0.95, eps: float = 1e-4):
        self.beta = beta
        self.eps = eps
        self.var_est = 1.0

    def update(self, e: float) -> float:
        self.var_est = self.beta * self.var_est + (1.0 - self.beta) * (e ** 2)
        return float(np.sqrt(self.var_est) + self.eps)

    def current_scale(self) -> float:
        return float(np.sqrt(self.var_est) + self.eps)

class CCAF:
    """
    Conformal-Controlled Adaptive Filter (CCAF 2.0)
    Combines:
      1. Conformal prediction interval output with distribution-free long-run coverage guarantees.
      2. Closed-loop step-size control driven by the ACI miscoverage state.
      3. Dead-band hysteresis controller (tau) to eliminate steady-state misadjustment tax.
      4. Strictly causal (a-priori) scale estimation to prevent outlier masking.
    """
    def __init__(
        self,
        num_taps: int,
        alpha: float = 0.10,          # Nominal error rate (1 - alpha coverage, e.g. 90%)
        gamma: float = 0.02,          # ACI adaptation step size
        window_size: int = 200,       # Calibration buffer length for quantile
        mu_min: float = 0.05,         # Floor step-size for stationary low EMSE
        mu_max: float = 0.80,         # Ceiling step-size for fast tracking (bounded < 2)
        p: float = 1.0,               # Control shaping exponent
        tau: float = 0.02,            # Dead-band threshold: suppresses false-alarm step-size inflation
        beta_scale: float = 0.95,     # Scale smoothing factor
        eps: float = 1e-6
    ):
        self.num_taps = num_taps
        self.alpha = alpha
        self.gamma = gamma
        self.window_size = window_size
        self.mu_min = mu_min
        self.mu_max = mu_max
        self.p = p
        self.tau = tau
        self.eps = eps

        # Internal states
        self.w = np.zeros(num_taps)
        self.a_n = alpha              # ACI state (adaptive error level)
        self.scale_est = RunningScaleEstimator(beta=beta_scale, eps=1e-4)
        self.score_buffer = deque(maxlen=window_size)
        self.recent_scale = 1.0
        self.prev_miss = 0.0

    def predict(self, u: np.ndarray):
        """
        Returns:
          y_hat: Point prediction
          y_lower: Lower bound of prediction interval
          y_upper: Upper bound of prediction interval
          q_val: Computed quantile width
        """
        y_hat = float(np.dot(self.w, u))

        # Effective quantile level = 1 - a_n (clipped to [0.01, 0.99])
        eff_level = float(np.clip(1.0 - self.a_n, 0.01, 0.99))

        if len(self.score_buffer) < 10:
            # Cold-start heuristic until buffer fills
            q_norm = 1.96
        else:
            scores = np.array(self.score_buffer)
            # Empirical quantile with finite-sample correction
            q_norm = float(np.quantile(scores, eff_level))

        # Strictly causal scale: use scale from previous iteration
        s_causal = self.recent_scale
        q_val = q_norm * s_causal
        y_lower = y_hat - q_val
        y_upper = y_hat + q_val

        return y_hat, y_lower, y_upper, q_val

    def update(self, u: np.ndarray, d: float):
        """
        Observe target d, update conformal state and filter weights.
        Scale estimation is strictly causal (a-priori).
        """
        # 1. Point prediction and a-priori error
        y_hat = float(np.dot(self.w, u))
        e = d - y_hat

        # 2. Strictly causal scale for normalization (prior to updating with current e)
        s_causal = self.recent_scale

        # 3. Normalized nonconformity score based on a-priori scale
        r_n = abs(e) / (s_causal + 1e-12)

        # Quantile threshold based on current buffer and a_n
        if len(self.score_buffer) < 10:
            q_norm = 1.96
        else:
            eff_level = float(np.clip(1.0 - self.a_n, 0.01, 0.99))
            q_norm = float(np.quantile(np.array(self.score_buffer), eff_level))

        # Conformal miss indicator
        m_n = 1.0 if r_n > q_norm else 0.0
        self.score_buffer.append(r_n)

        # 4. ACI update recursion: a_{n+1} = a_n + gamma * (alpha - m_n)
        self.a_n = float(np.clip(self.a_n + self.gamma * (self.alpha - m_n), 0.001, 0.999))

        # 5. Coverage-driven step-size control with Dead-Band Hysteresis
        # In steady state, stochastic 10% misses keep (alpha - a_n) <= tau, so c_n = 0 and mu_n = mu_min.
        # Upon non-stationary plant disruptions, misses accumulate, (alpha - a_n) > tau, elevating mu_n.
        raw_deficit = (self.alpha - self.a_n - self.tau) / max(self.alpha - self.tau, 1e-6)
        c_n = float(np.clip(raw_deficit, 0.0, 1.0))
        mu_n = self.mu_min + (self.mu_max - self.mu_min) * (c_n ** self.p)

        # 6. NLMS weight update
        norm_sq = float(np.dot(u, u))
        self.w = self.w + (mu_n * e / (norm_sq + self.eps)) * u

        # 7. Measurement update for running scale (for next iteration n+1)
        s_next = self.scale_est.update(e)
        self.recent_scale = s_next
        self.prev_miss = m_n

        return {
            "e": e,
            "m_n": m_n,
            "a_n": self.a_n,
            "c_n": c_n,
            "mu_n": mu_n,
            "s_n": s_next
        }

    def run(self, U: np.ndarray, d: np.ndarray):
        num_samples = len(d)
        y_hat = np.zeros(num_samples)
        y_lower = np.zeros(num_samples)
        y_upper = np.zeros(num_samples)
        e = np.zeros(num_samples)
        m = np.zeros(num_samples)
        a_hist = np.zeros(num_samples)
        mu_hist = np.zeros(num_samples)
        W_history = np.zeros((num_samples, self.num_taps))

        for n in range(num_samples):
            u_n = U[n]
            d_n = d[n]

            yh, yl, yu, _ = self.predict(u_n)
            y_hat[n] = yh
            y_lower[n] = yl
            y_upper[n] = yu

            res = self.update(u_n, d_n)
            e[n] = res["e"]
            m[n] = res["m_n"]
            a_hist[n] = res["a_n"]
            mu_hist[n] = res["mu_n"]
            W_history[n] = self.w.copy()

        return {
            "y_hat": y_hat,
            "y_lower": y_lower,
            "y_upper": y_upper,
            "e": e,
            "m": m,
            "a_hist": a_hist,
            "mu_hist": mu_hist,
            "W_history": W_history
        }

class DecoupledACINLMS(CCAF):
    """
    Ablation baseline: ACI computes prediction intervals on top of NLMS,
    but the step size is FIXED at mu_fixed (no closed loop feedback).
    """
    def __init__(self, num_taps: int, mu_fixed: float = 0.05, **kwargs):
        super().__init__(num_taps, mu_min=mu_fixed, mu_max=mu_fixed, tau=0.0, **kwargs)

    def update(self, u: np.ndarray, d: float):
        res = super().update(u, d)
        # Override step size to fixed value
        norm_sq = float(np.dot(u, u))
        self.w = self.w - (res["mu_n"] * res["e"] / (norm_sq + self.eps)) * u
        self.w = self.w + (self.mu_min * res["e"] / (norm_sq + self.eps)) * u
        res["mu_n"] = self.mu_min
        return res
