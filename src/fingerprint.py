"""
Fingerprint extraction (constellation + pairwise hashing).
Usage (example):
    python src/fingerprint.py path/to/audio.wav "My Song Title"
This will print summary hashes and (optionally) insert them into the DB using db.py.
"""
import sys
import hashlib
import numpy as np
import librosa
import scipy.ndimage as ndi
import sqlite3
from pathlib import Path
from typing import List, Tuple

# adjust these params to trade robustness vs size
# SR = 22050                # librosa default (we can downsample)
# N_FFT = 4096              # FFT window size
# HOP_LENGTH = 512          # hop between STFT frames
# PEAK_NEIGHBORHOOD_SIZE = 20  # local neighborhood for peak picking (in spectrogram bins)
# AMP_MIN = 10              # minimum amplitude in log-scaled spectrogram to be a peak (tweakable)
# FAN_VALUE = 15            # how many nearby peaks to pair with (Shazam-like)
SR = 22050
N_FFT = 2048
HOP_LENGTH = 256
PEAK_NEIGHBORHOOD_SIZE = 8
AMP_MIN = 40
FAN_VALUE = 10

def load_audio(path: str, sr: int = SR):
    y, sr = librosa.load(path, sr=sr, mono=True)
    return y, sr

def spectrogram(y: np.ndarray, sr: int = SR, n_fft: int = N_FFT, hop_length: int = HOP_LENGTH):
    S = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop_length))
    S_db = librosa.amplitude_to_db(S, ref=np.max)
    return S_db

def find_peaks(S_db: np.ndarray,
               neighborhood_size: int = PEAK_NEIGHBORHOOD_SIZE,
               amp_min: float = AMP_MIN) -> List[Tuple[int,int]]:
    """
    Return list of peaks as (freq_bin, time_bin)
    """
    # apply maximum filter
    footprint = np.ones((neighborhood_size, neighborhood_size))
    local_max = ndi.maximum_filter(S_db, footprint=footprint) == S_db

    # background mask (ignore very low energy)
    background = (S_db < -amp_min)  # because S_db is negative-valued dB
    detected_peaks = local_max & ~background

    peaks_idx = np.argwhere(detected_peaks)
    # peaks_idx rows: [freq_bin, time_bin]
    peaks = [tuple(p) for p in peaks_idx]
    return peaks

def generate_hashes(peaks: List[Tuple[int,int]],
                    fan_value: int = FAN_VALUE,
                    fan_time_delta_max: int = 200) -> List[Tuple[str,int]]:
    """
    For each peak, pair with up to fan_value subsequent peaks within a time window
    and produce hashes. Returns list of (hash_hex, t1) where t1 is time bin of the anchor.
    """
    # sort peaks by time (time_bin is second element)
    peaks_sorted = sorted(peaks, key=lambda x: x[1])
    hashes = []
    for i, anchor in enumerate(peaks_sorted):
        f1, t1 = anchor
        # pair with next points
        for j in range(1, fan_value + 1):
            if i + j >= len(peaks_sorted):
                break
            f2, t2 = peaks_sorted[i + j]
            dt = t2 - t1
            if dt <= 0 or dt > fan_time_delta_max:
                continue
            # create a compact string and hash it
            hstring = f"{f1}|{f2}|{dt}"
            h = hashlib.sha1(hstring.encode("utf-8")).hexdigest()[:20]
            hashes.append((h, t1))
    return hashes

def fingerprint_file(audio_path: str,
                     song_name: str = None,
                     do_store: bool = False,
                     db_path: str = "fingerprints.db") -> List[Tuple[str,int]]:
    audio_path = Path(audio_path)
    if not audio_path.exists():
        raise FileNotFoundError(audio_path)

    y, sr = load_audio(str(audio_path))
    S_db = spectrogram(y, sr=sr)
    peaks = find_peaks(S_db)
    hashes = generate_hashes(peaks)

    print(f"File: {audio_path.name}")
    print(f"Sample rate: {sr}, duration: {len(y)/sr:.2f}s")
    print(f"Spectrogram shape: {S_db.shape}")
    print(f"Found peaks: {len(peaks)}, generated hashes: {len(hashes)}")

    if do_store and song_name:
        # lazy import db helper to store
        from src.db import FingerprintDB
        db = FingerprintDB(db_path)
        song_id = db.insert_song(song_name, str(audio_path))
        db.insert_fingerprints(song_id, hashes)
        print(f"Stored {len(hashes)} fingerprints for song_id={song_id} in {db_path}")

    # return hashes for quick testing
    return hashes

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python src/fingerprint.py path/to/audio.wav [Song Name]")
        sys.exit(1)
    audio_p = sys.argv[1]
    song_n = sys.argv[2] if len(sys.argv) > 2 else None
    fingerprint_file(audio_p, song_name=song_n, do_store=bool(song_n))
