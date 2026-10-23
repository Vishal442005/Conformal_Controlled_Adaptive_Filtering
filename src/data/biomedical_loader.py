import os
import numpy as np
import wfdb

def load_ecg_noise_cancellation_data(num_samples: int = 15000, num_taps: int = 16):
    """
    Load clean ECG from MIT-BIH record 118 and Electrode Motion (EM) noise from NSTDB.
    Constructs adaptive noise cancellation configuration:
      Primary input d(n): clean ECG + EM noise (signal of interest is clean ECG)
      Reference input u(n): correlated noise source (filtered / delayed EM noise)
    """
    ecg_rec_path = os.path.abspath("data/ecg/mitdb/118")
    noise_rec_path = os.path.abspath("data/ecg/em")

    rec_ecg = wfdb.rdrecord(ecg_rec_path)
    rec_noise = wfdb.rdrecord(noise_rec_path)

    clean_ecg = rec_ecg.p_signal[:num_samples, 0]
    em_noise = rec_noise.p_signal[:num_samples, 0]

    # Normalize clean ECG and noise to realistic amplitudes
    clean_ecg = (clean_ecg - np.mean(clean_ecg)) / (np.std(clean_ecg) + 1e-12)
    em_noise = (em_noise - np.mean(em_noise)) / (np.std(em_noise) + 1e-12)

    # Reference correlated noise input u(n): slightly shifted/filtered version of EM noise
    u_seq = np.roll(em_noise, shift=2)
    u_seq[:2] = 0.0

    # Build regressor matrix U
    U = np.zeros((num_samples, num_taps))
    for i in range(num_taps):
        if i == 0:
            U[:, i] = u_seq
        else:
            U[i:, i] = u_seq[:-i]

    # Primary desired signal d(n)
    d = clean_ecg + em_noise

    return {
        "U": U,
        "d": d,
        "clean_ecg": clean_ecg,
        "em_noise": em_noise,
        "num_samples": num_samples,
        "num_taps": num_taps
    }

def load_eeg_artifact_removal_data(epoch_idx: int = 0, snr_db: float = 0.0, num_taps: int = 16):
    """
    Loads EEGdenoiseNet epochs.
    Constructs ocular artifact (EOG) cancellation task:
      Primary input d(n): clean EEG + scaled EOG artifact
      Reference input u(n): EOG channel
    """
    eeg_epochs = np.load("data/eeg/EEG_all_epochs.npy")
    eog_epochs = np.load("data/eeg/EOG_all_epochs.npy")

    # Pick single epoch (typically 512 samples at 256 Hz)
    clean_eeg = eeg_epochs[epoch_idx % len(eeg_epochs)]
    raw_eog = eog_epochs[epoch_idx % len(eog_epochs)]

    # Repeat or tile to obtain 2048 samples if needed
    repeats = 4
    clean_eeg = np.tile(clean_eeg, repeats)
    raw_eog = np.tile(raw_eog, repeats)
    num_samples = len(clean_eeg)

    # Scale artifact according to specified SNR
    eeg_pwr = np.var(clean_eeg)
    eog_pwr = np.var(raw_eog)
    scale_factor = np.sqrt(eeg_pwr / ((10.0 ** (snr_db / 10.0)) * (eog_pwr + 1e-12)))
    scaled_eog = raw_eog * scale_factor

    d = clean_eeg + scaled_eog
    u_seq = raw_eog / (np.std(raw_eog) + 1e-12)

    U = np.zeros((num_samples, num_taps))
    for i in range(num_taps):
        if i == 0:
            U[:, i] = u_seq
        else:
            U[i:, i] = u_seq[:-i]

    return {
        "U": U,
        "d": d,
        "clean_eeg": clean_eeg,
        "scaled_eog": scaled_eog,
        "num_samples": num_samples,
        "num_taps": num_taps
    }
