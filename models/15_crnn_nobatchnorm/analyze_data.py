import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Add parent directory to path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../data')))
import utils

def analyze_data():
    print("Loading data...")
    df = utils.load_and_clean_data("../../")

    # Filter for RELAX and NOISE
    relax_df = df[df['Label'] == 'RELAX']
    noise_df = df[df['Label'] == 'NOISE']

    print(f"RELAX samples: {len(relax_df)}")
    print(f"NOISE samples: {len(noise_df)}")

    # Plot raw value distributions
    plt.figure(figsize=(12, 6))
    sns.histplot(relax_df['RawValue'], label='RELAX', color='blue', alpha=0.5, kde=True)
    sns.histplot(noise_df['RawValue'], label='NOISE', color='red', alpha=0.5, kde=True)
    plt.title("Distribution of Raw Values: RELAX vs NOISE")
    plt.legend()
    plt.savefig("dist_comparison.png")

    # Look at a few windows
    X_raw, y = utils.create_windows(df)

    relax_windows = X_raw[y == 'RELAX']
    noise_windows = X_raw[y == 'NOISE']

    if len(relax_windows) > 0 and len(noise_windows) > 0:
        plt.figure(figsize=(12, 6))
        plt.plot(relax_windows[0], label='RELAX Example', alpha=0.7)
        plt.plot(noise_windows[0], label='NOISE Example', alpha=0.7)
        plt.title("Example Waveforms (1s)")
        plt.legend()
        plt.savefig("waveform_comparison.png")

        # Average FFT
        def get_avg_fft(windows):
            ffts = []
            for w in windows:
                # Remove DC
                w = w - np.mean(w)
                ffts.append(np.abs(np.fft.rfft(w)))
            return np.mean(ffts, axis=0)

        relax_fft = get_avg_fft(relax_windows)
        noise_fft = get_avg_fft(noise_windows)
        freqs = np.fft.rfftfreq(1000, 1/1000)

        plt.figure(figsize=(12, 6))
        plt.plot(freqs, relax_fft, label='RELAX Avg Spectrum')
        plt.plot(freqs, noise_fft, label='NOISE Avg Spectrum')
        plt.title("Average Frequency Spectrum")
        plt.xlabel("Frequency (Hz)")
        plt.ylabel("Magnitude")
        plt.legend()
        plt.savefig("spectrum_comparison.png")

if __name__ == "__main__":
    analyze_data()
