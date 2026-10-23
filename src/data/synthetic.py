import numpy as np

def generate_synthetic_data(
    scenario: str = "S1",
    num_taps: int = 32,
    num_samples: int = 20000,
    snr_db: float = 20.0,
    rho: float = 0.9,
    step_change_sample: int = 8000,
    random_walk_std: float = 1e-4,
    noise_jump_factor: float = 10.0,
    student_t_df: float = 3.0,
    outlier_prob: float = 0.05,
    outlier_scale: float = 10.0,
    seed: int = 42
):
    """
    Generate synthetic input signal u(n), desired signal d(n),
    true optimal weights w_o(n), and clean signal y_clean(n).

    Scenarios:
      S1: Stationary Gaussian, white input
      S2: Stationary Gaussian, coloured AR(1) input
      S3: Abrupt plant change at step_change_sample
      S4: Random-walk plant drift
      S5: Time-varying noise variance (piecewise step jump)
      S6: Non-Gaussian stress (Student-t or Gaussian-mixture outliers)
    """
    rng = np.random.default_rng(seed)

    # 1. Generate Input Signal u(n)
    if scenario == "S2":
        # AR(1) coloured input: u(n) = rho*u(n-1) + sqrt(1 - rho^2)*xi(n)
        xi = rng.standard_normal(num_samples)
        u_seq = np.zeros(num_samples)
        u_seq[0] = xi[0]
        std_scale = np.sqrt(1.0 - rho**2)
        for i in range(1, num_samples):
            u_seq[i] = rho * u_seq[i-1] + std_scale * xi[i]
    else:
        # Stationary white Gaussian input
        u_seq = rng.standard_normal(num_samples)

    # Construct input regressor matrix U: shape (num_samples, num_taps)
    # where U[n] = [u(n), u(n-1), ..., u(n - num_taps + 1)]
    U = np.zeros((num_samples, num_taps))
    for i in range(num_taps):
        if i == 0:
            U[:, i] = u_seq
        else:
            U[i:, i] = u_seq[:-i]

    # 2. Generate True System Weight Trajectory w_o(n)
    # Initial plant: normalized random vector
    w0 = rng.standard_normal(num_taps)
    w0 /= np.linalg.norm(w0)

    W_opt = np.zeros((num_samples, num_taps))

    if scenario == "S3":
        # Abrupt plant change (sign-flip / perturbation at step_change_sample)
        W_opt[:step_change_sample, :] = w0
        W_opt[step_change_sample:, :] = -w0
    elif scenario == "S4":
        # Random walk: w_o(n+1) = w_o(n) + q(n), q(n) ~ N(0, sigma_q^2 I)
        w_curr = w0.copy()
        for n in range(num_samples):
            W_opt[n, :] = w_curr
            q = rng.normal(0, random_walk_std, size=num_taps)
            w_curr = w_curr + q
    else:
        # Stationary plant
        W_opt[:, :] = w0

    # 3. Clean Plant Output
    y_clean = np.sum(U * W_opt, axis=1)

    # Compute signal variance to set nominal observation noise variance sigma_v^2
    sig_power = np.var(y_clean)
    sigma_v = np.sqrt(sig_power / (10.0 ** (snr_db / 10.0)))

    # 4. Generate Measurement Noise v(n)
    if scenario == "S5":
        # Time-varying noise variance (jumps up at n = step_change_sample)
        v = rng.normal(0, sigma_v, size=num_samples)
        v[step_change_sample:] *= np.sqrt(noise_jump_factor)
    elif scenario == "S6":
        # Non-Gaussian stress: mixture of Student-t and impulsive outliers
        # Base Student-t noise scaled by sigma_v
        v_t = rng.standard_t(df=student_t_df, size=num_samples) * sigma_v
        # Additive impulsive outliers
        is_outlier = rng.uniform(0, 1, size=num_samples) < outlier_prob
        outliers = rng.normal(0, sigma_v * outlier_scale, size=num_samples) * is_outlier
        v = v_t + outliers
    else:
        # Standard AWGN
        v = rng.normal(0, sigma_v, size=num_samples)

    # Desired signal
    d = y_clean + v

    return {
        "U": U,
        "d": d,
        "W_opt": W_opt,
        "y_clean": y_clean,
        "v": v,
        "sigma_v": sigma_v,
        "snr_db": snr_db
    }
