import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input as mobilenet_preprocess
from tensorflow.keras.applications.resnet50 import preprocess_input as resnet_preprocess
import cv2
from sklearn.metrics import confusion_matrix

# Add parent directory to path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../data')))
import utils

def generate_ensemble_matrix():
    print("--- Generating Ensemble Confusion Matrix ---")

    # 1. Load Data
    base_dir = "../data/"
    df = utils.load_and_clean_data(base_dir)
    X_raw, y = utils.create_windows(df)

    # Encode labels
    from sklearn.preprocessing import LabelEncoder
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    classes = le.classes_

    # Split Data
    indices = np.arange(len(X_raw))
    X_train_idx, X_test_idx, y_train, y_test = utils.get_data_splits(indices, y_enc)
    X_test_raw = X_raw[X_test_idx]

    # 2. Load Models & Predict
    model_probs = {}

    # Random Forest
    try:
        rf_path = "../06_random_forest/model.pkl"
        if os.path.exists(rf_path):
            print("Loading Random Forest...")
            rf = joblib.load(rf_path)
            X_test_feat_a = utils.extract_features_set_a(X_test_raw)
            model_probs['RF'] = rf.predict_proba(X_test_feat_a)
    except Exception as e:
        print(f"Error loading RF: {e}")

    # MobileNet
    try:
        mn_path = "../10_mobilenet/model.h5"
        if os.path.exists(mn_path):
            print("Loading MobileNet...")
            mn = load_model(mn_path)
            specs = utils.extract_features_set_c(X_test_raw)
            X_test_mobile = []
            for spec in specs:
                resized = cv2.resize(spec, (96, 96))
                norm = (resized - resized.min()) / (resized.max() - resized.min()) * 255
                norm = norm.astype(np.uint8)
                rgb = cv2.cvtColor(norm, cv2.COLOR_GRAY2RGB)
                pre = mobilenet_preprocess(rgb.astype(np.float32))
                X_test_mobile.append(pre)
            model_probs['MN'] = mn.predict(np.array(X_test_mobile), verbose=0)
    except Exception as e:
        print(f"Error loading MobileNet: {e}")

    # ResNet
    try:
        rn_path = "../11_resnet/model.h5"
        if os.path.exists(rn_path):
            print("Loading ResNet...")
            rn = load_model(rn_path)
            specs = utils.extract_features_set_c(X_test_raw)
            X_test_resnet = []
            for spec in specs:
                resized = cv2.resize(spec, (96, 96))
                norm = (resized - resized.min()) / (resized.max() - resized.min()) * 255
                norm = norm.astype(np.uint8)
                rgb = cv2.cvtColor(norm, cv2.COLOR_GRAY2RGB)
                pre = resnet_preprocess(rgb.astype(np.float32))
                X_test_resnet.append(pre)
            model_probs['RN'] = rn.predict(np.array(X_test_resnet), verbose=0)
    except Exception as e:
        print(f"Error loading ResNet: {e}")

    # 3. Ensemble (Mega)
    if 'RF' in model_probs and 'MN' in model_probs and 'RN' in model_probs:
        print("Calculating Mega Ensemble...")
        ensemble_probs = (model_probs['RF'] + model_probs['MN'] + model_probs['RN']) / 3
        preds = np.argmax(ensemble_probs, axis=1)

        # 4. Generate Matrix
        cm = confusion_matrix(y_test, preds)

        plt.figure(figsize=(6, 5))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=classes, yticklabels=classes)
        plt.title('Confusion Matrix: Ensemble (Mega)')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        png_filename = "cm_12_ensemble.png"
        plt.savefig(png_filename)
        plt.close()
        print(f"Saved {png_filename}")

        # 5. Update results.md
        results_path = "results.md"
        with open(results_path, 'r') as f:
            content = f.read()

        image_markdown = f"\n![Confusion Matrix]({png_filename})\n"
        if png_filename not in content:
            print("Appending image link to results.md...")
            with open(results_path, 'a') as f:
                f.write(image_markdown)
    else:
        print("Could not load all models for ensemble.")

if __name__ == "__main__":
    generate_ensemble_matrix()
