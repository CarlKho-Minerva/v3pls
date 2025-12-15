import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import time

# Add parent directory to path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../data')))
import utils

def train_and_evaluate():
    print("--- Model 2: Rolling Variance (Energy) ---")

    # 1. Load Data
    base_dir = "../data/"
    df = utils.load_and_clean_data(base_dir)

    # 2. Windowing
    X_raw, y = utils.create_windows(df)
    print(f"Total Windows: {len(X_raw)}")

    # 3. Split Data
    X_train, X_test, y_train, y_test = utils.get_data_splits(X_raw, y)

    # 4. Feature Extraction (Variance)
    def get_variance(windows):
        features = []
        for w in windows:
            features.append(np.var(w))
        return np.array(features)

    X_train_var = get_variance(X_train)
    X_test_var = get_variance(X_test)

    # 5. Train (Find Optimal Threshold)
    # Target: CLENCH = 1, Others = 0
    y_train_binary = (y_train == 'CLENCH').astype(int)
    y_test_binary = (y_test == 'CLENCH').astype(int)

    best_threshold = 0
    best_acc = 0

    # Variance values can be large, so we scan a wide range
    thresholds = np.linspace(0, np.max(X_train_var), 100)

    for t in thresholds:
        y_pred = (X_train_var > t).astype(int)
        acc = accuracy_score(y_train_binary, y_pred)
        if acc > best_acc:
            best_acc = acc
            best_threshold = t

    print(f"Optimal Threshold: {best_threshold:.2f} (Train Acc: {best_acc:.4f})")

    # 6. Evaluate on Test Set
    start_time = time.time()
    y_pred_binary = (X_test_var > best_threshold).astype(int)
    inference_time = (time.time() - start_time) / len(X_test) * 1000 # ms per sample

    test_acc = accuracy_score(y_test_binary, y_pred_binary)
    print(f"Test Accuracy: {test_acc:.4f}")
    print(f"Inference Latency: {inference_time:.4f} ms")

    # 7. Generate Report
    report = f"""# Model 2: Rolling Variance Results

## Performance
*   **Accuracy:** {test_acc:.4f}
*   **Optimal Threshold:** {best_threshold:.2f}
*   **Inference Latency:** {inference_time:.4f} ms

## Classification Report (Binary: Clench vs. Rest)
```
{classification_report(y_test_binary, y_pred_binary, target_names=['Rest', 'Clench'])}
```

## Confusion Matrix
```
{confusion_matrix(y_test_binary, y_pred_binary)}
```
"""

    with open("results.md", "w") as f:
        f.write(report)

    # 8. Visualization
    plt.figure(figsize=(10, 6))
    sns.histplot(x=X_test_var, hue=y_test, element="step", stat="density", common_norm=False)
    plt.axvline(best_threshold, color='r', linestyle='--', label=f'Threshold ({best_threshold:.0f})')
    plt.title("Signal Variance Distribution by Class")
    plt.xlabel("Variance (Energy)")
    plt.legend()
    plt.savefig("viz.png")
    print("Results and visualization saved.")

if __name__ == "__main__":
    train_and_evaluate()
