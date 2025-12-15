#!/usr/bin/env python3
"""
Generate Confusion Matrices for Models 1-5 (heuristic/classical) and create
a 3x6 grid combining them with existing CM images for Models 6-17.
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import seaborn as sns
from sklearn.metrics import confusion_matrix
from sklearn.preprocessing import LabelEncoder
import joblib

# Add parent directory to path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import utils

def generate_models_1_to_5():
    """Generate confusion matrices for Models 1-5."""

    print("=" * 60)
    print("GENERATING CONFUSION MATRICES FOR MODELS 1-5")
    print("=" * 60)

    # 1. Load Data
    base_dir = "../"
    df = utils.load_and_clean_data(base_dir)
    X_raw, y = utils.create_windows(df)

    # Encode labels
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    classes = le.classes_  # ['CLENCH', 'NOISE', 'RELAX']

    # Split Data (Same seed as training)
    indices = np.arange(len(X_raw))
    X_train_idx, X_test_idx, y_train, y_test = utils.get_data_splits(indices, y_enc)
    X_test_raw = X_raw[X_test_idx]
    y_test_labels = y[X_test_idx]  # String labels for 3-class

    # Pre-compute features (Set A only - no spectrograms needed)
    print("\nExtracting features...")
    X_test_feat_a = utils.extract_features_set_a(X_test_raw)

    # ========== MODEL 1: Simple Thresholding ==========
    print("\n[1/5] Threshold...")
    def get_max_amplitude(windows):
        return np.array([np.max(np.abs(w - np.mean(w))) for w in windows])

    X_test_max = get_max_amplitude(X_test_raw)
    threshold = 800  # Approximate from training
    preds_binary = (X_test_max > threshold).astype(int)
    preds_1 = np.where(preds_binary == 1, 'CLENCH', 'RELAX')

    cm1 = confusion_matrix(y_test_labels, preds_1, labels=classes)
    save_cm(cm1, classes, '01_threshold', 'Threshold')

    # ========== MODEL 2: Rolling Variance ==========
    print("[2/5] Rolling Variance...")
    def get_variance(windows):
        return np.array([np.var(w) for w in windows])

    X_test_var = get_variance(X_test_raw)
    var_threshold = 50000  # Approximate
    preds_binary = (X_test_var > var_threshold).astype(int)
    preds_2 = np.where(preds_binary == 1, 'CLENCH', 'RELAX')

    cm2 = confusion_matrix(y_test_labels, preds_2, labels=classes)
    save_cm(cm2, classes, '02_variance', 'Variance')

    # ========== MODEL 3: Logistic Regression ==========
    print("[3/5] Logistic Regression...")
    model_3 = joblib.load("03_logreg/model.pkl")
    preds_3 = model_3.predict(X_test_feat_a)

    cm3 = confusion_matrix(y_test_labels, preds_3, labels=classes)
    save_cm(cm3, classes, '03_logreg', 'LogReg')

    # ========== MODEL 4: KNN ==========
    print("[4/5] KNN...")
    model_4 = joblib.load("04_knn/model.pkl")
    preds_4 = model_4.predict(X_test_feat_a)

    cm4 = confusion_matrix(y_test_labels, preds_4, labels=classes)
    save_cm(cm4, classes, '04_knn', 'KNN')

    # ========== MODEL 5: SVM ==========
    print("[5/5] SVM...")
    model_5 = joblib.load("05_svm/model.pkl")
    preds_5 = model_5.predict(X_test_feat_a)

    cm5 = confusion_matrix(y_test_labels, preds_5, labels=classes)
    save_cm(cm5, classes, '05_svm', 'SVM')

    print("\nModels 1-5 complete!")
    return classes


def save_cm(cm, classes, model_key, model_name):
    """Save confusion matrix as PNG."""
    plt.figure(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=classes, yticklabels=classes)
    plt.title(f'CM: {model_name}', fontsize=10, fontweight='bold')
    plt.ylabel('True')
    plt.xlabel('Predicted')

    cm_path = f"../../arXiv_submission_clean/cm_{model_key}.png"
    plt.savefig(cm_path, dpi=100, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {cm_path}")


def create_grid_from_existing():
    """Create a 3x6 grid by loading saved CM images."""

    print("\n" + "=" * 60)
    print("CREATING 3x6 CONFUSION MATRIX GRID FROM EXISTING IMAGES")
    print("=" * 60)

    arxiv_dir = "../../arXiv_submission_clean"

    # Model display names and corresponding CM files
    models = [
        ('01_threshold', 'Threshold'),
        ('02_variance', 'Variance'),
        ('03_logreg', 'LogReg'),
        ('04_knn', 'KNN'),
        ('05_svm', 'SVM'),
        ('06_random_forest', 'RandomForest'),
        ('07_pca_logreg', 'PCA+LogReg'),
        ('08_mlp', 'MLP'),
        ('09b_cnn_aug', 'CNN+Aug'),
        ('10_mobilenet', 'MobileNetV2'),
        ('11_resnet', 'ResNet50'),
        ('12_ensemble', 'Ensemble'),
        ('13_xgboost', 'XGBoost'),
        ('14_baseline', 'CRNN'),
        ('15_nobatchnorm', 'CRNN-NoBN'),
        ('16_attention', 'CRNN+Attn'),
        ('17_maxcrnn', 'MaxCRNN'),
        ('18_maxcrnn', 'MaxCRNN (Aug)'),
    ]

    # Create figure (3 rows x 6 cols = 18 slots, 17 models + 1 empty)
    fig, axes = plt.subplots(3, 6, figsize=(24, 12))
    fig.suptitle('Confusion Matrix Comparison (All 17 Models)', fontsize=18, fontweight='bold')

    for idx, (model_key, model_name) in enumerate(models):
        row, col = idx // 6, idx % 6
        ax = axes[row, col]

        # Find the CM image
        cm_path = os.path.join(arxiv_dir, f"cm_{model_key}.png")

        if os.path.exists(cm_path):
            img = mpimg.imread(cm_path)
            ax.imshow(img)
            ax.set_title(f'{idx+1}. {model_name}', fontsize=11, fontweight='bold')
        else:
            ax.text(0.5, 0.5, f'{model_name}\n(No CM)', ha='center', va='center',
                    fontsize=12, transform=ax.transAxes)
            ax.set_title(f'{idx+1}. {model_name}', fontsize=11, fontweight='bold')

        ax.axis('off')

    # Hide the 18th (empty) subplot
    axes[2, 5].axis('off')

    plt.tight_layout(rect=[0, 0.02, 1, 0.96])

    # Save
    output_path = os.path.join(arxiv_dir, "viz_cm_all18.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"\nSaved grid: {output_path}")


if __name__ == "__main__":
    classes = generate_models_1_to_5()
    create_grid_from_existing()
    print("\nDone!")
