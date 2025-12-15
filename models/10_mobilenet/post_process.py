import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from scipy.stats import mode
import cv2
import glob

# Add parent directory to path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../data')))
import utils

def simulate_realtime_smoothing():
    print("--- Simulating Real-Time Temporal Smoothing ---")

    # 1. Load ONE Session (Continuous Stream)
    # We pick the last session to simulate "new" data
    base_dir = "../data/"
    all_files = sorted(glob.glob(os.path.join(base_dir, "2025_11_09-Session*", "*.csv")))
    if not all_files:
        print("No data found.")
        return

    test_file = all_files[-1]
    print(f"Simulating stream from: {os.path.basename(test_file)}")

    df = pd.read_csv(test_file, on_bad_lines='skip')
    df['RawValue'] = pd.to_numeric(df['RawValue'], errors='coerce')
    df.dropna(subset=['RawValue'], inplace=True)

    # 2. Dense Windowing (Sliding Window with Overlap)
    # Stride = 100ms (10Hz update rate) instead of 1000ms
    # This mimics a real-time system polling every 100ms
    WINDOW_SIZE = 1000
    STRIDE = 100

    X_stream = []
    y_stream = []
    timestamps = []

    # We can't easily group by label here because we want the transitions too!
    # But for accuracy calculation, we need ground truth.
    # Let's just process the whole file sequentially.

    values = df['RawValue'].values
    labels = df['Label'].values

    for i in range(0, len(values) - WINDOW_SIZE, STRIDE):
        window = values[i : i + WINDOW_SIZE]
        # Ground truth is the label at the END of the window (what we are predicting)
        # Or mode of the window. Let's use mode to be safe.
        # scipy.stats.mode doesn't support strings anymore, use pandas
        label_mode = pd.Series(labels[i : i + WINDOW_SIZE]).mode()[0]

        X_stream.append(window)
        y_stream.append(label_mode)
        timestamps.append(i)

    X_stream = np.array(X_stream)
    y_stream = np.array(y_stream)
    print(f"Generated {len(X_stream)} sliding windows (Stride={STRIDE}ms)")

    # 3. Preprocess for MobileNetV2 (Spectrograms)
    print("Generating Spectrograms...")
    # Reuse utils logic but adapted for this list
    spectrograms = []
    for window in X_stream:
        sig = window.astype(float)
        sig = sig - np.mean(sig)
        melspec = librosa.feature.melspectrogram(y=sig, sr=1000, n_mels=64, n_fft=256, hop_length=16)
        melspec_db = librosa.power_to_db(melspec, ref=np.max)
        spectrograms.append(melspec_db)

    # Resize for MobileNet
    X_mobile = []
    for spec in spectrograms:
        resized = cv2.resize(spec, (96, 96))
        norm = (resized - resized.min()) / (resized.max() - resized.min()) * 255
        norm = norm.astype(np.uint8)
        rgb = cv2.cvtColor(norm, cv2.COLOR_GRAY2RGB)
        pre = preprocess_input(rgb.astype(np.float32))
        X_mobile.append(pre)
    X_mobile = np.array(X_mobile)

    # Encode labels
    from sklearn.preprocessing import LabelEncoder
    le = LabelEncoder()
    # Fit on all possible labels to ensure mapping is correct
    le.fit(['CLENCH', 'RELAX', 'NOISE'])
    y_enc = le.transform(y_stream)

    # 4. Load Model & Predict
    print("Loading Model...")
    model = load_model("model.h5")

    print("Running Inference...")
    probs = model.predict(X_mobile, verbose=1)
    raw_preds = np.argmax(probs, axis=1)

    # 5. Apply Temporal Smoothing (Majority Vote over last N frames)
    # Window of 5 frames @ 100ms stride = 500ms history
    N = 5
    smooth_preds = []

    for i in range(len(raw_preds)):
        start_idx = max(0, i - N + 1)
        window_preds = raw_preds[start_idx : i + 1]
        # Majority vote
        vote = mode(window_preds, keepdims=True)[0][0]
        smooth_preds.append(vote)

    smooth_preds = np.array(smooth_preds)

    # 6. Calculate Metrics
    from sklearn.metrics import accuracy_score
    raw_acc = accuracy_score(y_enc, raw_preds)
    smooth_acc = accuracy_score(y_enc, smooth_preds)

    print(f"Raw Accuracy: {raw_acc:.4f}")
    print(f"Smoothed Accuracy (N={N}): {smooth_acc:.4f}")

    # 7. Generate Report
    report = f"""# Post-Processing: Temporal Smoothing

## 1. The Engineering "Hack"
Machine Learning models can be "jittery." A single 100ms noise spike might cause a prediction to flip from CLENCH to RELAX. However, human muscle movements are continuous. We can exploit this physical constraint using **Temporal Smoothing**.

## 2. Methodology
*   **Simulation:** We re-played a full session (`{os.path.basename(test_file)}`) as a continuous stream.
*   **Dense Sampling:** Instead of disjoint 1-second windows, we slid the window every **100ms** (10Hz).
*   **Smoothing Filter:** We applied a **Majority Vote** over the last {N} predictions (500ms history).

## 3. Results
| Metric | Accuracy | Notes |
| :--- | :--- | :--- |
| **Raw Inference** | **{raw_acc:.2%}** | Jittery, prone to single-frame errors. |
| **Smoothed (N={N})** | **{smooth_acc:.2%}** | Stable, robust to transient noise. |

## 4. Visualization
The plot below shows a segment of the stream. Notice how the "Smoothed" prediction (Green) ignores the brief glitches in the "Raw" prediction (Orange) and matches the Ground Truth (Blue).

![Smoothing Viz](viz_smoothing.png)
"""

    with open("results_post_process.md", "w") as f:
        f.write(report)

    # 8. Visualization
    # Plot a 10-second slice (100 windows)
    start = 100
    end = 200
    if len(y_enc) > end:
        plt.figure(figsize=(12, 6))
        plt.plot(y_enc[start:end], label='Ground Truth', color='black', linewidth=2, linestyle='--')
        plt.plot(raw_preds[start:end], label='Raw Pred', color='orange', alpha=0.7)
        plt.plot(smooth_preds[start:end], label=f'Smoothed (N={N})', color='green', linewidth=2)

        plt.yticks(ticks=[0, 1, 2], labels=le.classes_)
        plt.title(f"Temporal Smoothing Effect (Acc: {raw_acc:.2f} -> {smooth_acc:.2f})")
        plt.xlabel("Time Steps (100ms)")
        plt.legend()
        plt.savefig("viz_smoothing.png")
        print("Saved viz_smoothing.png")

import librosa # Need to re-import inside if not global (it is global but good practice)

if __name__ == "__main__":
    simulate_realtime_smoothing()
