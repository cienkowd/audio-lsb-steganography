import numpy as np
import pytest

from stego import config
from stego.metrics import calculate_metrics
from stego.steganography import LSBSteganography


@pytest.fixture
def signal():
    rng = np.random.default_rng(0)
    return rng.integers(-32768, 32767, size=(44100, 2), dtype=np.int16)


@pytest.fixture(autouse=True)
def restore_lsb_count():
    original = config.LSB_COUNT
    yield
    config.LSB_COUNT = original


@pytest.mark.parametrize("lsb_count", [1, 2, 3, 4])
@pytest.mark.parametrize("message", ["hello", "Zażółć gęślą jaźń", "x" * 5000])
def test_roundtrip(signal, lsb_count, message):
    config.LSB_COUNT = lsb_count
    stego = LSBSteganography.embed_message(signal, message)
    assert stego.shape == signal.shape
    assert stego.dtype == signal.dtype
    assert LSBSteganography.extract_message(stego) == message


def test_original_signal_untouched(signal):
    before = signal.copy()
    LSBSteganography.embed_message(signal, "secret")
    np.testing.assert_array_equal(signal, before)


@pytest.mark.parametrize("lsb_count", [1, 2, 4])
def test_only_low_bits_change(signal, lsb_count):
    config.LSB_COUNT = lsb_count
    stego = LSBSteganography.embed_message(signal, "y" * 1000)
    diff = np.abs(signal.astype(np.int32) - stego.astype(np.int32))
    assert diff.max() < 2 ** lsb_count


def test_message_too_long_raises():
    tiny = np.zeros(40, dtype=np.int16)
    with pytest.raises(ValueError, match="too long"):
        LSBSteganography.embed_message(tiny, "this does not fit")


def test_capacity_boundary():
    samples = np.zeros(32 + 8 * 4, dtype=np.int16)  # header + exactly 4 bytes at 1 bit/sample
    stego = LSBSteganography.embed_message(samples, "abcd")
    assert LSBSteganography.extract_message(stego) == "abcd"
    with pytest.raises(ValueError):
        LSBSteganography.embed_message(samples, "abcde")


def test_extract_from_clean_signal_does_not_return_garbage():
    loud = np.full(1000, -1, dtype=np.int16)  # all LSBs set -> header decodes to a huge length
    with pytest.raises(ValueError, match="No valid message"):
        LSBSteganography.extract_message(loud)


def test_metrics_identical_signals(signal):
    assert calculate_metrics(signal, signal) == (float("inf"), float("inf"))


def test_each_extra_bit_costs_about_6_db(signal):
    """Full-capacity embedding: PSNR should drop by ~6 dB per extra LSB."""
    psnr = {}
    for k in (1, 2, 4):
        config.LSB_COUNT = k
        n_chars = LSBSteganography.capacity(signal) // 8
        stego = LSBSteganography.embed_message(signal, "a" * n_chars)
        psnr[k], _ = calculate_metrics(signal, stego)
    assert psnr[1] > psnr[2] > psnr[4]
    assert 4 < psnr[1] - psnr[2] < 8
    assert 16 < psnr[1] - psnr[4] < 24
