# metrics.py
import numpy as np


def calculate_metrics(original, modified):
    """Oblicza PSNR i SNR dla sygnałów 16-bit."""
    orig = original.astype(np.float64)
    mod = modified.astype(np.float64)

    mse = np.mean((orig - mod) ** 2)

    if mse == 0:
        return float('inf'), float('inf')

    max_val = 32767.0  # Zakres int16

    # Peak Signal-to-Noise Ratio
    psnr = 10 * np.log10((max_val ** 2) / mse)

    # Signal-to-Noise Ratio
    signal_power = np.mean(orig ** 2)

    if signal_power == 0:
        snr = float('-inf')
    else:
        snr = 10 * np.log10(signal_power / mse)

    return psnr, snr