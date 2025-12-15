import sys
import os
import numpy as np
import pandas as pd
import joblib
import glob
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input as mobilenet_preprocess
from tensorflow.keras.applications.resnet50 import preprocess_input as resnet_preprocess
from sklearn.metrics import confusion_matrix
import cv2

# Add parent directory to path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import utils

import matplotlib.pyplot as plt
import seaborn as sns

def generate_matrices():
    print("--- Generating Confusion Matrices for All Models ---")

    # 1. Load Data
    base_dir = "../"
    df = utils.load_and_clean_data(base_dir)
    X_raw, y = utils.create_windows(df)

    # Encode labels
    from sklearn.preprocessing import LabelEncoder
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    classes = le.classes_

    # Split Data (Same seed as training)
    indices = np.arange(len(X_raw))
    X_train_idx, X_test_idx, y_train, y_test = utils.get_data_splits(indices, y_enc)
    X_test_raw = X_raw[X_test_idx]

    # Pre-compute features
    print("Extracting features...")
    X_test_feat_a = utils.extract_features_set_a(X_test_raw)
    X_test_feat_b = utils.extract_features_set_b(X_test_raw)
    X_test_specs = utils.extract_features_set_c(X_test_raw)

    # List of models to process
    models_dir = "."
    model_folders = sorted([f for f in os.listdir(models_dir) if os.path.isdir(f) and not f.startswith('.')])

    # Filter for models 06 and above (and 13_xgboost)
    target_models = [f for f in model_folders if (f >= "06_random_forest" or "xgboost" in f)]
    print(f"Target Models: {target_models}")

    for folder in target_models:
        print(f"\nProcessing {folder}...")
        results_path = os.path.join(folder, "results.md")

        if not os.path.exists(results_path):
            print(f"  No results.md found in {folder}, skipping.")
            continue

        preds = None

        # Determine model type and predict
        try:
            pkl_path = os.path.join(folder, "model.pkl")
            h5_path = os.path.join(folder, "model.h5")

            if os.path.exists(pkl_path):
                print(f"  Loading PKL model...")
                model = joblib.load(pkl_path)
                # XGBoost might need dataframe or array depending on version, usually array is safe
                # But feature names mismatch can be an issue if trained on DF.
                # Let's assume Set A features are compatible.
                if 'pca' in folder:
                     # PCA model expects raw features, it has PCA inside pipeline?
                     # Wait, 07_pca_logreg likely has a pipeline.
                     preds = model.predict(X_test_feat_a)
                else:
                     preds = model.predict(X_test_feat_a)

                # Handle string predictions
                if len(preds) > 0 and isinstance(preds[0], str):
                    preds = le.transform(preds)

            elif os.path.exists(h5_path):
                print(f"  Loading H5 model...")
                model = load_model(h5_path)

                if 'mlp' in folder:
                    probs = model.predict(X_test_feat_b, verbose=0)
                    preds = np.argmax(probs, axis=1)
                elif 'cnn' in folder:
                    X_cnn = X_test_feat_b.reshape((X_test_feat_b.shape[0], X_test_feat_b.shape[1], 1))
                    probs = model.predict(X_cnn, verbose=0)
                    preds = np.argmax(probs, axis=1)
                elif 'mobilenet' in folder:
                    X_mobile = []
                    for spec in X_test_specs:
                        resized = cv2.resize(spec, (96, 96))
                        norm = (resized - resized.min()) / (resized.max() - resized.min()) * 255
                        norm = norm.astype(np.uint8)
                        rgb = cv2.cvtColor(norm, cv2.COLOR_GRAY2RGB)
                        pre = mobilenet_preprocess(rgb.astype(np.float32))
                        X_mobile.append(pre)
                    probs = model.predict(np.array(X_mobile), verbose=0)
                    preds = np.argmax(probs, axis=1)
                elif 'resnet' in folder:
                    X_resnet = []
                    for spec in X_test_specs:
                        resized = cv2.resize(spec, (96, 96))
                        norm = (resized - resized.min()) / (resized.max() - resized.min()) * 255
                        norm = norm.astype(np.uint8)
                        rgb = cv2.cvtColor(norm, cv2.COLOR_GRAY2RGB)
                        pre = resnet_preprocess(rgb.astype(np.float32))
                        X_resnet.append(pre)
                    probs = model.predict(np.array(X_resnet), verbose=0)
                    preds = np.argmax(probs, axis=1)

            else:
                print(f"  No model file found in {folder}, skipping.")
                continue

            # Generate Confusion Matrix
            cm = confusion_matrix(y_test, preds)

            # Save as PNG
            plt.figure(figsize=(6, 5))
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=classes, yticklabels=classes)
            plt.title(f'Confusion Matrix: {folder}')
            plt.ylabel('True Label')
            plt.xlabel('Predicted Label')
            png_filename = f"cm_{folder}.png"
            png_path = os.path.join(folder, png_filename)
            plt.savefig(png_path)
            plt.close()
            print(f"  Saved {png_filename}")

            # Update results.md to include the image
            with open(results_path, 'r') as f:
                content = f.read()

            image_markdown = f"\n![Confusion Matrix]({png_filename})\n"

            if png_filename not in content:
                print("  Appending image link to results.md...")
                # Append after the text matrix if it exists, or at the end
                if "```" in content:
                    # Find the last closing backtick of the matrix block
                    last_backtick = content.rfind("```")
                    content = content[:last_backtick+3] + image_markdown + content[last_backtick+3:]
                else:
                    content += image_markdown

                with open(results_path, 'w') as f:
                    f.write(content)

        except Exception as e:
            print(f"  Error processing {folder}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    generate_matrices()
