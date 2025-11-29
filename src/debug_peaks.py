# diagnostic script — save as src/debug_peaks.py
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

# import your current functions & params from fingerprint.py
from src.fingerprint import (
    load_audio,
    spectrogram,
    find_peaks,
    SR,
    N_FFT,
    HOP_LENGTH,
    PEAK_NEIGHBORHOOD_SIZE,
    AMP_MIN,
    FAN_VALUE,
)

def pretty_print_params():
    print("Current fingerprint parameters:")
    print(f" SR = {SR}")
    print(f" N_FFT = {N_FFT}")
    print(f" HOP_LENGTH = {HOP_LENGTH}")
    print(f" PEAK_NEIGHBORHOOD_SIZE = {PEAK_NEIGHBORHOOD_SIZE}")
    print(f" AMP_MIN (dB threshold) = {AMP_MIN}")
    print(f" FAN_VALUE = {FAN_VALUE}")
    print()

def analyze(path: str):
    p = Path(path)
    if not p.exists():
        print("File not found:", p)
        return

    y, sr = load_audio(str(p))
    print(f"Loaded {p.name} — sample_rate={sr}, duration={len(y)/sr:.2f}s")

    S_db = spectrogram(y, sr=sr, n_fft=N_FFT, hop_length=HOP_LENGTH)
    print(f"Spectrogram shape (freq_bins x time_bins): {S_db.shape}")
    print(f"Spectrogram stats (dB): min={S_db.min():.2f}, max={S_db.max():.2f}, mean={S_db.mean():.2f}")
    print()

    peaks = find_peaks(S_db,
                       neighborhood_size=PEAK_NEIGHBORHOOD_SIZE,
                       amp_min=AMP_MIN)
    print(f"Detected peaks: {len(peaks)}")
    if len(peaks) == 0:
        # show the loudest bins so we know if any energy exists
        flat = S_db.flatten()
        top_idx = np.argsort(flat)[-30:][::-1]
        print("Top 30 spectrogram bin dB values (loudest):")
        for idx in top_idx:
            val = flat[idx]
            freq_bin = idx // S_db.shape[1]
            time_bin = idx % S_db.shape[1]
            print(f"  freq_bin={freq_bin:4d} time_bin={time_bin:4d} dB={val:.2f}")
    else:
        # print the first 40 peaks with their dB values
        print("First 40 peaks (freq_bin, time_bin, dB):")
        for i, (f, t) in enumerate(peaks[:40]):
            print(f"  {i+1:3d}: freq_bin={f:4d} time_bin={t:4d} dB={S_db[f,t]:.2f}")

    # save a visualization so you can inspect
    out_png = p.parent / "recording_spectrogram_peaks.png"
    plt.figure(figsize=(12, 6))
    plt.title(f"Spectrogram + peaks — {p.name}")
    # display spectrogram (transpose so time is x-axis)
    plt.imshow(S_db, origin="lower", aspect="auto")
    if len(peaks) > 0:
        freqs = [f for f, _ in peaks]
        times = [t for _, t in peaks]
        plt.scatter(times, freqs, marker='x', linewidths=0.5, s=12)
    plt.xlabel("Time bins")
    plt.ylabel("Freq bins")
    plt.colorbar(label="dB")
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    plt.close()
    print()
    print("Saved spectrogram + peaks image to:", out_png)

if __name__ == "__main__":
    pretty_print_params()
    if len(sys.argv) < 2:
        print("Usage: python -m src.debug_peaks path/to/audio.wav")
        sys.exit(1)
    analyze(sys.argv[1])
