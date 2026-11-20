import numpy as np

INT16_MAX = 32767.0


def calculate_metrics(original, modified):
    """Return (PSNR, SNR) in dB for 16-bit signals."""
    orig = original.astype(np.float64)
    mod = modified.astype(np.float64)

    mse = np.mean((orig - mod) ** 2)
    if mse == 0:
        return float("inf"), float("inf")

    psnr = 10 * np.log10(INT16_MAX ** 2 / mse)

    signal_power = np.mean(orig ** 2)
    snr = float("-inf") if signal_power == 0 else 10 * np.log10(signal_power / mse)

    return psnr, snr
