# Audio LSB Steganography

> Hides text messages in WAV audio by rewriting the least significant bits of each sample, with SNR/PSNR quality analysis.

![tests](https://github.com/cienkowd/audio-lsb-steganography/actions/workflows/tests.yml/badge.svg)

A desktop app (Tkinter) that embeds a UTF-8 message into a 16-bit PCM WAV file and reads it back. Each sample gives up 1, 2 or 4 of its lowest bits to the message; a 32-bit header at the start of the signal stores the message length, so decoding needs nothing but the stego file.

## How it works

1. The message is encoded to UTF-8 and split into bits.
2. A 32-bit length header is prepended.
3. For every sample, the lowest *k* bits are cleared and replaced with the next *k* message bits (`sample & ~mask | bits`).
4. Decoding reads the header first, checks it fits the signal's capacity (so a clean file is rejected instead of returning garbage), then reads exactly that many bits.

Capacity: `samples × channels × k − 32` bits. A 3-second stereo clip at 44.1 kHz holds ~33 KB of text at 1 bit/sample.

## Quality vs. capacity

Measured on a 3 s, 440 Hz sine at half amplitude (mono, 44.1 kHz):

| Bits per sample | Capacity | PSNR (full capacity) | PSNR (1000-char message) |
|---|---|---|---|
| 1 | 16.5 KB | 93.3 dB | 105.5 dB |
| 2 | 33.1 KB | 87.3 dB | 102.5 dB |
| 4 | 66.1 KB | 73.8 dB | 92.0 dB |

Each extra bit costs roughly 6 dB, as expected from doubling the maximum error per sample. The noise is inaudible at 1–2 bits; at 4 bits it can be heard on quiet passages and pure tones. 4-bit embedding also leaves a statistical trace (the *pairs of values* effect in the sample histogram), which is how simple LSB steganalysis detects it.

## Run

```bash
pip install -r requirements.txt
python -m stego.gui
```

Load a 16-bit PCM WAV, pick the number of bits per sample, type a message, **Encode**, then **Save WAV**. **Decode** reads a message from the loaded file (use the same bits-per-sample setting).

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

The suite checks encode/decode round trips for 1–4 bits per sample (including multi-byte UTF-8 and long messages), that only the low bits change, capacity limits, rejection of files without a message, and the ~6 dB/bit quality drop.

## Project layout

| File | Content |
|---|---|
| `stego/steganography.py` | Embedding and extraction |
| `stego/metrics.py` | PSNR and SNR |
| `stego/config.py` | Bits per sample, encoding, header size |
| `stego/gui.py` | Tkinter GUI with spectrogram and difference plot |
| `tests/` | pytest suite |

---

Built for the Multimedia Techniques course, Applied Computer Science, Warsaw University of Technology.
