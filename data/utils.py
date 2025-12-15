import pandas as pd
import numpy as np
import os
import glob

from sklearn.model_selection import train_test_split

# Configuration
WINDOW_SIZE = 1000  # 1 second at 1000Hz
STRIDE = 1000       # Non-overlapping for training
SAMPLE_RATE = 1000
RANDOM_SEED = 1738    # Fixed seed for reproducibility

def load_and_clean_data(base_dir):
    """
    Loads and cleans EMG data from session files.
    """
    all_files = glob.glob(os.path.join(base_dir, "2025_11_09-Session*", "*.csv"))
    print(f"Found {len(all_files)} session files.")

    df_list = []
    for filename in all_files:
        try:
            # Read CSV, handling potential bad lines
            temp_df = pd.read_csv(filename, on_bad_lines='skip')

            # Basic Validation: Check columns
            if list(temp_df.columns) == ['Label', 'Timestamp', 'RawValue']:
                # Ensure numeric
                temp_df['RawValue'] = pd.to_numeric(temp_df['RawValue'], errors='coerce')
                temp_df.dropna(subset=['RawValue'], inplace=True)
                df_list.append(temp_df)
        except Exception as e:
            print(f"Error reading {filename}: {e}")

    if not df_list:
        print("No valid data files found!")
        return pd.DataFrame()

    full_df = pd.concat(df_list, ignore_index=True)
    print(f"Total Samples: {len(full_df)}")
    return full_df

def create_windows(df, window_size=WINDOW_SIZE, stride=STRIDE):
    """
    Segments continuous data into windows.
    """
    X = []
    y = []

    # Group by Label to ensure pure windows
    for label, group in df.groupby('Label'):
        values = group['RawValue'].values

        for i in range(0, len(values) - window_size, stride):
            window = values[i : i + window_size]
            X.append(window)
            y.append(label)

    return np.array(X), np.array(y)

def extract_features_set_a(X_raw):
    """
    Set A: Statistical Features (for LogReg, SVM, RF)
    Returns: DataFrame with [MAV, STD, MAX, ZCR]
    """
    features = []
    for window in X_raw:
        # Center the window to remove DC offset (~2200)
        centered = window - np.mean(window)

        # Mean Absolute Value (of the AC component)
        mav = np.mean(np.abs(centered))

        # Standard Deviation
        std = np.std(window) # std is invariant to mean shift, so raw or centered is fine

        # Max Amplitude (Relative to mean)
        max_val = np.max(np.abs(centered))

        # Zero Crossing Rate
        zcr = ((centered[:-1] * centered[1:]) < 0).sum()

        features.append([mav, std, max_val, zcr])

    return pd.DataFrame(features, columns=['MAV', 'STD', 'MAX', 'ZCR'])

def extract_features_set_b(X_raw):
    """
    Set B: Raw Sequence (for 1D CNN)
    Returns: Normalized raw vectors [0, 1]
    """
    if len(X_raw) == 0: return X_raw
    # Min-Max Normalization across the entire dataset
    # Note: This preserves the relative shape but squashes the ~2000 offset into the [0,1] range.
    global_min = X_raw.min()
    global_max = X_raw.max()
    return (X_raw - global_min) / (global_max - global_min)

def extract_features_set_c(X_raw, sample_rate=SAMPLE_RATE):
    """
    Set C: Mel-Spectrograms (for Transfer Learning)
    Returns: List of 2D arrays (images)
    """
    spectrograms = []
    for window in X_raw:
        # Convert to float and CENTER the signal
        sig = window.astype(float)
        sig = sig - np.mean(sig)

        import librosa
        # Compute Mel Spectrogram
        melspec = librosa.feature.melspectrogram(
            y=sig,
            sr=sample_rate,
            n_mels=64,
            n_fft=256,
            hop_length=16
        )

        # Convert to dB (Log scale)
        import librosa
        melspec_db = librosa.power_to_db(melspec, ref=np.max)
        spectrograms.append(melspec_db)

    return np.array(spectrograms)

def get_data_splits(X, y, test_size=0.2, random_state=RANDOM_SEED):
    """
    Performs stratified train/test split.
    """
    return train_test_split(X, y, test_size=test_size, stratify=y, random_state=random_state)
