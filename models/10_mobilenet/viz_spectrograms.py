import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import librosa
import librosa.display

# Add parent directory to path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../data')))
import utils

def generate_spectrogram_viz():
    print("--- Generating Spectrogram Visualizations ---")

    # 1. Load Data
    base_dir = "../data/"
    df = utils.load_and_clean_data(base_dir)

    # 2. Windowing
    X_raw, y = utils.create_windows(df)

    # 3. Find one good example of each class
    classes = ['CLENCH', 'RELAX', 'NOISE'] # Adjust based on actual labels

    plt.figure(figsize=(15, 5))

    for i, label in enumerate(classes):
        # Find indices for this label
        indices = np.where(y == label)[0]
        if len(indices) == 0:
            continue

        # Pick a random one (or the first one)
        idx = indices[10] # Pick 10th to avoid start artifacts
        signal = X_raw[idx]

        # Ensure float32
        signal = signal.astype(np.float32)

        # Compute Mel Spectrogram (Same params as utils.py)
        # n_fft=2048, hop_length=512, n_mels=64 for 1000 samples
        # 1000 samples @ 1000Hz = 1 sec
        S = librosa.feature.melspectrogram(y=signal, sr=1000, n_fft=256, hop_length=16, n_mels=64)
        S_dB = librosa.power_to_db(S, ref=np.max)

        plt.subplot(1, 3, i+1)
        librosa.display.specshow(S_dB, sr=1000, hop_length=16, x_axis='time', y_axis='mel')
        plt.title(f"Class: {label}")
        plt.colorbar(format='%+2.0f dB')

    plt.tight_layout()
    plt.savefig("spectrogram_samples.png")
    print("Saved spectrogram_samples.png")

if __name__ == "__main__":
    generate_spectrogram_viz()
