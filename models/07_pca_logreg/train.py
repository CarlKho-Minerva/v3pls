import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LogisticRegression
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import time
import joblib

# Add parent directory to path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../data')))
import utils

def train_and_evaluate():
    print("--- Model 7: PCA + Logistic Regression ---")

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

    # 5. Train (Pipeline: Scaler -> PCA -> LogReg)
    print("Training PCA + LogReg...")
    # We use 2 components for visualization purposes, but also to test if 2D is enough
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('pca', PCA(n_components=2)),
        ('clf', LogisticRegression(random_state=utils.RANDOM_SEED))
    ])

    pipeline.fit(X_train, y_train)

    # 6. Evaluate
    start_time = time.time()
    y_pred = pipeline.predict(X_test)
    inference_time = (time.time() - start_time) / len(X_test) * 1000 # ms per sample

    test_acc = accuracy_score(y_test, y_pred)
    print(f"Test Accuracy: {test_acc:.4f}")
    print(f"Inference Latency: {inference_time:.4f} ms")

    # 7. Save Model
    joblib.dump(pipeline, "model.pkl")

    # 8. Generate Report
    explained_variance = pipeline.named_steps['pca'].explained_variance_ratio_
    report = f"""# Model 7: PCA + Logistic Regression Results

## Performance
*   **Accuracy:** {test_acc:.4f}
*   **Inference Latency:** {inference_time:.4f} ms
*   **PCA Components:** 2
*   **Explained Variance:** {np.sum(explained_variance):.4f} ({explained_variance})

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

    # 9. Visualization (2D PCA Scatter Plot)
    plt.figure(figsize=(10, 8))

    # Transform test data for plotting
    X_test_pca = pipeline.named_steps['pca'].transform(pipeline.named_steps['scaler'].transform(X_test))
    df_pca = pd.DataFrame(X_test_pca, columns=['PC1', 'PC2'])
    df_pca['Label'] = y_test

    sns.scatterplot(data=df_pca, x='PC1', y='PC2', hue='Label', style='Label', palette='viridis')
    plt.title(f"PCA Projection (Acc: {test_acc:.2f})")
    plt.savefig("viz.png")
    print("Results and visualization saved.")

if __name__ == "__main__":
    train_and_evaluate()
