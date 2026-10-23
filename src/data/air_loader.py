import os
import numpy as np
from scipy.io import loadmat, wavfile

def load_air_impulse_response(file_path: str, target_length: int = 128) -> np.ndarray:
    """
    Load an Acoustic Impulse Response (AIR) from a .mat, .wav, or .npy file.
    Truncates or zero-pads to target_length and normalizes energy.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"AIR file not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".mat":
        data = loadmat(file_path)
        # Typical AIR database mat files contain 'h_air' or similar variable
        for key in ["h_air", "air", "h", "rir", "impulse_response"]:
            if key in data:
                h = np.squeeze(data[key])
                break
        else:
            # Fallback: take first non-private array
            non_dunder = [v for k, v in data.items() if not k.startswith("__") and isinstance(v, np.ndarray)]
            if non_dunder:
                h = np.squeeze(non_dunder[0])
            else:
                raise ValueError(f"Could not identify impulse response vector in {file_path}")
    elif ext == ".wav":
        fs, h = wavfile.read(file_path)
        if h.ndim > 1:
            h = h[:, 0]  # mono
        h = h.astype(np.float64) / (np.max(np.abs(h)) + 1e-12)
    elif ext == ".npy":
        h = np.load(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")

    h = np.squeeze(h)
    if len(h) >= target_length:
        h = h[:target_length]
    else:
        h = np.pad(h, (0, target_length - len(h)), mode='constant')

    # Energy normalize
    norm = np.linalg.norm(h)
    if norm > 0:
        h = h / norm
    return h

def generate_aec_simulation_data(
    air_path_initial: str,
    air_path_changed: str = None,
    num_samples: int = 20000,
    num_taps: int = 128,
    snr_db: float = 20.0,
    change_sample: int = 10000,
    speech_signal: np.ndarray = None,
    seed: int = 42
):
    """
    Generate Acoustic Echo Cancellation (AEC) simulation data with real AIR paths.
    """
    rng = np.random.default_rng(seed)

    # 1. Input far-end signal (speech or colored noise)
    if speech_signal is not None and len(speech_signal) >= num_samples:
        u_seq = speech_signal[:num_samples].astype(np.float64)
        u_seq = u_seq / (np.std(u_seq) + 1e-12)
    else:
        # AR(1) proxy for speech
        rho = 0.95
        xi = rng.standard_normal(num_samples)
        u_seq = np.zeros(num_samples)
        u_seq[0] = xi[0]
        std_scale = np.sqrt(1.0 - rho**2)
        for i in range(1, num_samples):
            u_seq[i] = rho * u_seq[i-1] + std_scale * xi[i]

    # Regressor matrix U
    U = np.zeros((num_samples, num_taps))
    for i in range(num_taps):
        if i == 0:
            U[:, i] = u_seq
        else:
            U[i:, i] = u_seq[:-i]

    # 2. Impulse response path(s)
    h1 = load_air_impulse_response(air_path_initial, target_length=num_taps)
    W_opt = np.tile(h1, (num_samples, 1))

    if air_path_changed and os.path.exists(air_path_changed):
        h2 = load_air_impulse_response(air_path_changed, target_length=num_taps)
        W_opt[change_sample:, :] = h2
    elif change_sample < num_samples:
        # Abrupt shift in acoustic path (e.g. mic/speaker position move)
        h2 = np.roll(h1, 4)
        W_opt[change_sample:, :] = h2

    # 3. Echo output + near-end background noise
    echo = np.sum(U * W_opt, axis=1)
    echo_power = np.var(echo)
    sigma_v = np.sqrt(echo_power / (10.0 ** (snr_db / 10.0)))
    noise = rng.normal(0, sigma_v, size=num_samples)

    d = echo + noise

    return {
        "U": U,
        "d": d,
        "W_opt": W_opt,
        "y_clean": echo,
        "v": noise,
        "sigma_v": sigma_v
    }
