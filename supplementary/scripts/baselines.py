import numpy as np

class BaseAdaptiveFilter:
    def __init__(self, num_taps: int):
        self.num_taps = num_taps
        self.w = np.zeros(num_taps)

    def predict(self, u: np.ndarray) -> float:
        return float(np.dot(self.w, u))

    def update(self, u: np.ndarray, d: float):
        raise NotImplementedError

    def run(self, U: np.ndarray, d: np.ndarray):
        num_samples = len(d)
        y_hat = np.zeros(num_samples)
        e = np.zeros(num_samples)
        W_history = np.zeros((num_samples, self.num_taps))

        for n in range(num_samples):
            u_n = U[n]
            d_n = d[n]
            y_hat[n] = self.predict(u_n)
            e[n] = d_n - y_hat[n]
            self.update(u_n, d_n)
            W_history[n] = self.w.copy()

        return {
            "y_hat": y_hat,
            "e": e,
            "W_history": W_history
        }

class LMSFilter(BaseAdaptiveFilter):
    def __init__(self, num_taps: int, mu: float = 0.01):
        super().__init__(num_taps)
        self.mu = mu

    def update(self, u: np.ndarray, d: float):
        y_hat = self.predict(u)
        e = d - y_hat
        self.w += self.mu * e * u
        return e

class NLMSFilter(BaseAdaptiveFilter):
    def __init__(self, num_taps: int, mu: float = 0.1, eps: float = 1e-6):
        super().__init__(num_taps)
        self.mu = mu
        self.eps = eps

    def update(self, u: np.ndarray, d: float):
        y_hat = self.predict(u)
        e = d - y_hat
        norm_sq = np.dot(u, u)
        self.w += (self.mu * e / (norm_sq + self.eps)) * u
        return e

class SignErrorLMS(BaseAdaptiveFilter):
    def __init__(self, num_taps: int, mu: float = 0.01):
        super().__init__(num_taps)
        self.mu = mu

    def update(self, u: np.ndarray, d: float):
        y_hat = self.predict(u)
        e = d - y_hat
        self.w += self.mu * np.sign(e) * u
        return e

class RLSFilter(BaseAdaptiveFilter):
    def __init__(self, num_taps: int, lmbda: float = 0.999, delta: float = 0.01):
        super().__init__(num_taps)
        self.lmbda = lmbda
        self.P = (1.0 / delta) * np.eye(num_taps)

    def update(self, u: np.ndarray, d: float):
        y_hat = self.predict(u)
        e = d - y_hat
        Pi_u = np.dot(self.P, u)
        denom = self.lmbda + np.dot(u, Pi_u)
        k = Pi_u / denom
        self.w += k * e
        self.P = (self.P - np.outer(k, Pi_u)) / self.lmbda
        return e

class AffineProjectionFilter(BaseAdaptiveFilter):
    def __init__(self, num_taps: int, order: int = 2, mu: float = 0.2, eps: float = 1e-4):
        super().__init__(num_taps)
        self.K = order
        self.mu = mu
        self.eps = eps
        self.U_mem = np.zeros((self.K, num_taps))
        self.d_mem = np.zeros(self.K)

    def update(self, u: np.ndarray, d: float):
        # Shift memory
        self.U_mem = np.roll(self.U_mem, shift=1, axis=0)
        self.U_mem[0] = u
        self.d_mem = np.roll(self.d_mem, shift=1)
        self.d_mem[0] = d

        e_vec = self.d_mem - np.dot(self.U_mem, self.w)
        R_reg = np.dot(self.U_mem, self.U_mem.T) + self.eps * np.eye(self.K)
        inv_e = np.linalg.solve(R_reg, e_vec)
        self.w += self.mu * np.dot(self.U_mem.T, inv_e)
        return e_vec[0]

class KwongJohnstonVSSLMS(BaseAdaptiveFilter):
    """
    Kwong & Johnston (1992) Variable Step-Size LMS
    mu(n+1) = alpha * mu(n) + gamma * e(n)^2 clipped to [mu_min, mu_max]
    """
    def __init__(self, num_taps: int, alpha: float = 0.97, gamma: float = 1e-3,
                 mu_min: float = 1e-4, mu_max: float = 0.5):
        super().__init__(num_taps)
        self.alpha = alpha
        self.gamma = gamma
        self.mu_min = mu_min
        self.mu_max = mu_max
        self.mu = mu_max

    def update(self, u: np.ndarray, d: float):
        y_hat = self.predict(u)
        e = d - y_hat
        norm_sq = float(np.dot(u, u))
        self.w += (self.mu * e / (norm_sq + 1e-4)) * u
        # Update step size for next iteration with numerical guard
        e_sq = float(min(abs(e), 100.0) ** 2)
        mu_next = self.alpha * self.mu + self.gamma * e_sq
        self.mu = float(np.clip(mu_next, self.mu_min, self.mu_max))
        return e

class BenestyNPVSSNLMS(BaseAdaptiveFilter):
    """
    Benesty et al. (2006) Nonparametric VSS-NLMS
    Automatically balances system distance and noise estimation without heuristic parameters.
    """
    def __init__(self, num_taps: int, eps: float = 1e-6, alpha_scale: float = 0.99):
        super().__init__(num_taps)
        self.eps = eps
        self.alpha_scale = alpha_scale
        self.sigma_e2 = 1.0
        self.sigma_v2 = 0.01  # running floor estimate

    def update(self, u: np.ndarray, d: float):
        y_hat = self.predict(u)
        e = d - y_hat
        norm_sq = np.dot(u, u)

        # Update power estimates
        self.sigma_e2 = self.alpha_scale * self.sigma_e2 + (1.0 - self.alpha_scale) * (e ** 2)
        # Track minimal noise floor
        if self.sigma_e2 < self.sigma_v2:
            self.sigma_v2 = self.sigma_e2
        else:
            self.sigma_v2 = 0.999 * self.sigma_v2 + 0.001 * self.sigma_e2

        # Nonparametric step size calculation: mu(n) = |1 - sigma_v / (sigma_e + eps)|
        p_ratio = np.sqrt(max(0.0, self.sigma_v2) / (self.sigma_e2 + self.eps))
        mu = max(0.0, min(1.0, abs(1.0 - p_ratio)))

        self.w += (mu * e / (norm_sq + self.eps)) * u
        return e

class ConvexCombinationNLMS(BaseAdaptiveFilter):
    """
    Arenas-Garcia et al. (2006) Convex combination of fast and slow NLMS filters
    """
    def __init__(self, num_taps: int, mu_fast: float = 0.8, mu_slow: float = 0.05,
                 mu_a: float = 0.5, eps: float = 1e-6):
        super().__init__(num_taps)
        self.filter_fast = NLMSFilter(num_taps, mu=mu_fast, eps=eps)
        self.filter_slow = NLMSFilter(num_taps, mu=mu_slow, eps=eps)
        self.a = 0.0  # mixing parameter before sigmoid
        self.mu_a = mu_a

    def predict(self, u: np.ndarray) -> float:
        y1 = self.filter_fast.predict(u)
        y2 = self.filter_slow.predict(u)
        lmbda = 1.0 / (1.0 + np.exp(-self.a))
        return lmbda * y1 + (1.0 - lmbda) * y2

    def update(self, u: np.ndarray, d: float):
        y1 = self.filter_fast.predict(u)
        y2 = self.filter_slow.predict(u)
        lmbda = 1.0 / (1.0 + np.exp(-self.a))
        y_hat = lmbda * y1 + (1.0 - lmbda) * y2
        e = d - y_hat

        # Update sub-filters
        self.filter_fast.update(u, d)
        self.filter_slow.update(u, d)

        # Gradient update on mixing parameter a
        grad = e * (y1 - y2) * lmbda * (1.0 - lmbda)
        self.a = float(np.clip(self.a + self.mu_a * grad, -4.0, 4.0))

        # Overall virtual weight vector for tracking metrics
        self.w = lmbda * self.filter_fast.w + (1.0 - lmbda) * self.filter_slow.w
        return e

class KalmanOracleFilter(BaseAdaptiveFilter):
    """
    Kalman filter oracle tracking time-varying weights with known noise statistics (sigma_v, sigma_q).
    """
    def __init__(self, num_taps: int, sigma_v: float, sigma_q: float = 0.0):
        super().__init__(num_taps)
        self.sigma_v2 = sigma_v ** 2
        self.Q = (sigma_q ** 2) * np.eye(num_taps)
        self.P = np.eye(num_taps)

    def update(self, u: np.ndarray, d: float):
        # Time update (prediction)
        # w_pred = w, P_pred = P + Q
        P_pred = self.P + self.Q

        # Measurement update
        y_hat = float(np.dot(self.w, u))
        e = d - y_hat
        Pu = np.dot(P_pred, u)
        innov_cov = float(np.dot(u, Pu) + self.sigma_v2)
        k = Pu / (innov_cov + 1e-12)

        self.w = self.w + k * e
        self.P = P_pred - np.outer(k, Pu)
        return e
