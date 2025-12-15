import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import time
import joblib

# Add parent directory to path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../data')))
import utils

def train_and_evaluate():
    print("--- Model 3: Logistic Regression ---")

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
    print("Training Logistic Regression...")
    model = LogisticRegression(max_iter=1000, random_state=utils.RANDOM_SEED)
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
    report = f"""# Model 3: Logistic Regression Results

## Performance
*   **Accuracy:** {test_acc:.4f}
*   **Inference Latency:** {inference_time:.4f} ms

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

    # 9. Visualization (Feature Importance - Coefficients)
    plt.figure(figsize=(10, 6))
    if len(model.classes_) == 2:
        coefs = model.coef_[0]
    else:
        coefs = np.mean(np.abs(model.coef_), axis=0)

    sns.barplot(x=X_features.columns, y=coefs)
    plt.title("Feature Importance (Logistic Regression Coefficients)")
    plt.ylabel("Mean Absolute Coefficient")
    plt.savefig("viz.png")
    print("Results and visualization saved.")

if __name__ == "__main__":
    train_and_evaluate()
