import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import time
import joblib

# Add parent directory to path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../data')))
import utils

def train_and_evaluate():
    print("--- Model 5: Support Vector Machine (SVM) ---")

    # 1. Load Data
    base_dir = "../data/"
    df = utils.load_and_clean_data(base_dir)

    # 2. Windowing
    X_raw, y = utils.create_windows(df)

    # 3. Feature Extraction (Set A)
    print("Extracting features...")
    X_features = utils.extract_features_set_a(X_raw)

    # 4. Split Data
    X_train, X_test, y_train, y_test = utils.get_data_splits(X_features, y)

    # 5. Train
    print("Training SVM (RBF Kernel)...")
    model = SVC(kernel='rbf', C=1.0, gamma='scale', random_state=utils.RANDOM_SEED)
    model.fit(X_train, y_train)

    # 6. Evaluate
    start_time = time.time()
    y_pred = model.predict(X_test)
    inference_time = (time.time() - start_time) / len(X_test) * 1000 # ms per sample

    test_acc = accuracy_score(y_test, y_pred)
    print(f"Test Accuracy: {test_acc:.4f}")
    print(f"Inference Latency: {inference_time:.4f} ms")

    # 7. Save Model
    joblib.dump(model, "model.pkl")

    # 8. Generate Report
    report = f"""# Model 5: SVM Results

## Performance
*   **Accuracy:** {test_acc:.4f}
*   **Inference Latency:** {inference_time:.4f} ms
*   **Kernel:** RBF

## Classification Report
```
{classification_report(y_test, y_pred)}
```

## Confusion Matrix
```
{confusion_matrix(y_test, y_pred)}
```
"""

    with open("results.md", "w") as f:
        f.write(report)

    # 9. Visualization (Confusion Matrix)
    plt.figure(figsize=(8, 6))
    sns.heatmap(confusion_matrix(y_test, y_pred), annot=True, fmt='d', cmap='Blues',
                xticklabels=model.classes_, yticklabels=model.classes_)
    plt.title("Confusion Matrix (SVM)")
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.savefig("viz.png")
    print("Results and visualization saved.")

if __name__ == "__main__":
    train_and_evaluate()
