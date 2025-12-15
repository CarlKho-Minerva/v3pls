import pandas as pd
import numpy as np
import joblib
import os
import sys
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# Add parent directory to path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../data')))
import utils

def train_xgboost():
    print("--- Training Model 13: XGBoost ---")

    # 1. Load Data
    base_dir = "../data/"
    df = utils.load_and_clean_data(base_dir)
    X_raw, y = utils.create_windows(df)

    # 2. Encode Labels
    from sklearn.preprocessing import LabelEncoder
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    classes = le.classes_
    print(f"Classes: {classes}")

    # 3. Split Data
    indices = np.arange(len(X_raw))
    X_train_idx, X_test_idx, y_train, y_test = utils.get_data_splits(indices, y_enc)

    X_train_raw = X_raw[X_train_idx]
    X_test_raw = X_raw[X_test_idx]

    # 4. Feature Extraction (Set A: Statistical)
    print("Extracting Feature Set A...")
    X_train = utils.extract_features_set_a(X_train_raw)
    X_test = utils.extract_features_set_a(X_test_raw)

    # 5. Train XGBoost
    # Using standard parameters, can be tuned later
    model = XGBClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        objective='multi:softprob',
        num_class=len(classes),
        random_state=42,
        n_jobs=-1
    )

    print("Fitting model...")
    model.fit(X_train, y_train)

    # 6. Evaluate
    preds = model.predict(X_test)
    acc = accuracy_score(y_test, preds)
    print(f"Test Accuracy: {acc:.4f}")

    print("\nClassification Report:")
    print(classification_report(y_test, preds, target_names=classes))

    # 7. Save Model
    joblib.dump(model, "model.pkl")
    print("Model saved to model.pkl")

    # 8. Generate Results Markdown (Initial Draft)
    results_content = f"""# Model 13: XGBoost Analysis

## 1. Abstract
XGBoost (Extreme Gradient Boosting) is the industry standard for tabular data. Unlike Random Forest (which builds trees in parallel), XGBoost builds trees sequentially, where each new tree corrects the errors of the previous ones. We hypothesized that this "boosting" mechanism would squeeze out more accuracy from the statistical features (Set A) than the Random Forest.

## 2. Quantitative Results
*   **Test Accuracy:** {acc*100:.2f}%
*   **Inference Latency:** TBD (Likely < 1ms)

## 3. Mathematical Formulation (#MLMath)
XGBoost minimizes a regularized objective function $\mathcal{{L}}(\phi)$:

$$
\mathcal{{L}}(\phi) = \sum_{{i}} l(\hat{{y}}_i, y_i) + \sum_{{k}} \Omega(f_k)
$$

Where:
*   $l$ is the differentiable loss function (e.g., Log Loss).
*   $\Omega(f_k) = \gamma T + \frac{{1}}{{2}}\lambda ||w||^2$ is the regularization term (penalizes tree complexity $T$ and leaf weights $w$).
*   The model is additive: $\hat{{y}}_i^{{(t)}} = \hat{{y}}_i^{{(t-1)}} + f_t(x_i)$.

## 4. Causal Mechanism (Gradient Boosting)
Why does it work?
*   **Error Correction:** If the first tree fails to classify a "weak clench" correctly, the second tree specifically targets that error (by weighting it higher).
*   **Regularization:** The $\Omega$ term prevents overfitting, which is crucial given our small dataset.

## 5. Spatial Visualization
Spatially, XGBoost carves the feature space into hyper-rectangles like Random Forest, but the boundaries are much more refined. It can create "steps" to approximate smooth curves, allowing it to model subtler decision boundaries than a single decision tree.

## 6. Confusion Matrix
```
{confusion_matrix(y_test, preds)}
```
"""

    with open("results.md", "w") as f:
        f.write(results_content)
    print("results.md created.")

if __name__ == "__main__":
    train_xgboost()
