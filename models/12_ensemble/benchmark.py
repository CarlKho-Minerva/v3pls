import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from sklearn.metrics import classification_report, accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier
import cv2
import librosa

# Add parent directory to path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../data')))
import utils

def benchmark_all_models():
    print("--- Comprehensive Benchmark & Disagreement Analysis ---")

    # 1. Load Data
    # We are running from 'data/models/11_ensemble/', so base_dir (data dir) is '../..'
    base_dir = "../.."
    print(f"DEBUG: base_dir = {os.path.abspath(base_dir)}")
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

    print(f"Test Set Size: {len(y_test)}")

    # Store predictions
    model_preds = {}

    # --- Phase 1 & 2: Classical Models ---
    classical_models = {
        '03_logreg': 'Logistic Regression',
        '04_knn': 'KNN',
        '05_svm': 'SVM',
        '06_random_forest': 'Random Forest',
        '07_pca_logreg': 'PCA + LogReg'
    }

    # Store probabilities for Soft Voting
    model_probs = {}

    X_test_feat_a = utils.extract_features_set_a(X_test_raw)

    for folder, name in classical_models.items():
        try:
            path = f"../{folder}/model.pkl"
            if os.path.exists(path):
                print(f"Evaluating {name}...")
                model = joblib.load(path)
                if 'PCA' in name:
                    preds = model.predict(X_test_feat_a)
                    # PCA LogReg might not support predict_proba easily if pipeline, skip for now
                else:
                    preds = model.predict(X_test_feat_a)
                    if hasattr(model, "predict_proba"):
                        probs = model.predict_proba(X_test_feat_a)
                        model_probs[name] = probs

                # Ensure preds are numeric
                if isinstance(preds[0], str):
                    preds = le.transform(preds)

                model_preds[name] = preds
        except Exception as e:
            print(f"Skipping {name}: {e}")

    # --- Phase 4 & 5: Deep Learning ---
    # MLP
    try:
        print("Evaluating MLP...")
        mlp_model = load_model("../08_mlp/model.h5")
        X_test_feat_b = utils.extract_features_set_b(X_test_raw)
        probs_mlp = mlp_model.predict(X_test_feat_b, verbose=0)
        preds_mlp = np.argmax(probs_mlp, axis=1)
        model_preds['MLP (Warning: Failed)'] = preds_mlp
    except Exception as e:
        print(f"Skipping MLP: {e}")

    # CNN
    try:
        print("Evaluating CNN...")
        cnn_model = load_model("../09_cnn/model.h5")
        # Reshape for CNN
        X_test_cnn = X_test_feat_b.reshape((X_test_feat_b.shape[0], X_test_feat_b.shape[1], 1))
        probs_cnn = cnn_model.predict(X_test_cnn, verbose=0)
        preds_cnn = np.argmax(probs_cnn, axis=1)
        model_preds['CNN (Warning: Failed)'] = preds_cnn
    except Exception as e:
        print(f"Skipping CNN: {e}")

    # MobileNet
    try:
        print("Evaluating MobileNetV2...")
        mn_model = load_model("../10_mobilenet/model.h5")

        # Preprocess
        specs = utils.extract_features_set_c(X_test_raw)
        X_test_mobile = []
        for spec in specs:
            resized = cv2.resize(spec, (96, 96))
            norm = (resized - resized.min()) / (resized.max() - resized.min()) * 255
            norm = norm.astype(np.uint8)
            rgb = cv2.cvtColor(norm, cv2.COLOR_GRAY2RGB)
            pre = preprocess_input(rgb.astype(np.float32))
            X_test_mobile.append(pre)
        X_test_mobile = np.array(X_test_mobile)

        probs_mn = mn_model.predict(X_test_mobile, verbose=0)
        model_probs['MobileNetV2'] = probs_mn
        preds_mn = np.argmax(probs_mn, axis=1)
        model_preds['MobileNetV2'] = preds_mn

    except Exception as e:
        print(f"Skipping MobileNetV2: {e}")

    # ResNet50
    try:
        print("Evaluating ResNet50...")
        rn_model = load_model("../12_resnet/model.h5")
        from tensorflow.keras.applications.resnet50 import preprocess_input as resnet_preprocess

        # Preprocess (Same resizing, different normalization)
        specs = utils.extract_features_set_c(X_test_raw)
        X_test_resnet = []
        for spec in specs:
            resized = cv2.resize(spec, (96, 96))
            norm = (resized - resized.min()) / (resized.max() - resized.min()) * 255
            norm = norm.astype(np.uint8)
            rgb = cv2.cvtColor(norm, cv2.COLOR_GRAY2RGB)
            # ResNet preprocess
            pre = resnet_preprocess(rgb.astype(np.float32))
            X_test_resnet.append(pre)
        X_test_resnet = np.array(X_test_resnet)

        probs_rn = rn_model.predict(X_test_resnet, verbose=0)
        model_probs['ResNet50'] = probs_rn
        preds_rn = np.argmax(probs_rn, axis=1)
        model_preds['ResNet50'] = preds_rn

    except Exception as e:
        print(f"Skipping ResNet50: {e}")

    # --- Ensembles (Soft Voting) ---
    print("\n--- Calculating Ensembles ---")
    if 'Random Forest' in model_probs and 'MobileNetV2' in model_probs:
        # Original Ensemble
        p_rf = model_probs['Random Forest']
        p_mn = model_probs['MobileNetV2']
        ensemble_orig = (p_rf + p_mn) / 2
        model_preds['Ensemble (RF + MobileNet)'] = np.argmax(ensemble_orig, axis=1)

    if 'Random Forest' in model_probs and 'ResNet50' in model_probs:
        # RF + ResNet
        p_rf = model_probs['Random Forest']
        p_rn = model_probs['ResNet50']
        ensemble_resnet = (p_rf + p_rn) / 2
        model_preds['Ensemble (RF + ResNet)'] = np.argmax(ensemble_resnet, axis=1)

    if 'Random Forest' in model_probs and 'MobileNetV2' in model_probs and 'ResNet50' in model_probs:
        # Mega Ensemble
        p_rf = model_probs['Random Forest']
        p_mn = model_probs['MobileNetV2']
        p_rn = model_probs['ResNet50']
        ensemble_mega = (p_rf + p_mn + p_rn) / 3
        model_preds['Ensemble (Mega: RF+MN+RN)'] = np.argmax(ensemble_mega, axis=1)

    # --- K-Fold Cross Validation (Random Forest) ---
    print("\n--- Performing 5-Fold CV on Random Forest (ML Rigor) ---")

    # We need the full training set for CV, not just the test set
    # Re-extract features for the WHOLE dataset
    X_all_feat_a = utils.extract_features_set_a(X_raw)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=1738)
    rf_cv = RandomForestClassifier(n_estimators=100, random_state=1738)

    cv_scores = cross_val_score(rf_cv, X_all_feat_a, y_enc, cv=cv, scoring='accuracy')
    print(f"RF 5-Fold CV Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")

    # --- Metrics Table ---
    metrics_data = []

    for name, preds in model_preds.items():
        acc = accuracy_score(y_test, preds)
        prec = precision_score(y_test, preds, average='weighted')
        rec = recall_score(y_test, preds, average='weighted')
        f1 = f1_score(y_test, preds, average='weighted')

        # Per class F1
        f1_per_class = f1_score(y_test, preds, average=None)

        row = {
            'Model': name,
            'Accuracy': acc,
            'Precision': prec,
            'Recall': rec,
            'F1-Score': f1,
            'F1 (Clench)': f1_per_class[le.transform(['CLENCH'])[0]],
            'F1 (Relax)': f1_per_class[le.transform(['RELAX'])[0]],
            'F1 (Noise)': f1_per_class[le.transform(['NOISE'])[0]]
        }
        metrics_data.append(row)

    df_metrics = pd.DataFrame(metrics_data).sort_values(by='Accuracy', ascending=False)
    print("\n--- Comprehensive Metrics ---")
    print(df_metrics)

    # Save Metrics
    df_metrics.to_csv("comprehensive_metrics.csv", index=False)

    # --- Disagreement Visualization (RF vs MobileNet) ---
    if 'Random Forest' in model_preds and 'MobileNetV2' in model_preds:
        preds_rf = model_preds['Random Forest']
        preds_mn = model_preds['MobileNetV2']

        disagreement_idx = np.where(preds_rf != preds_mn)[0]
        print(f"\nFound {len(disagreement_idx)} disagreements.")

        # Pick 2 interesting cases
        # Case 1: RF Correct, MN Wrong
        rf_wins = [i for i in disagreement_idx if preds_rf[i] == y_test[i]]
        # Case 2: MN Correct, RF Wrong
        mn_wins = [i for i in disagreement_idx if preds_mn[i] == y_test[i]]

        plt.figure(figsize=(12, 8))

        def plot_case(idx, row_idx, title_prefix):
            # Raw Signal
            signal = X_test_raw[idx]
            true_label = classes[y_test[idx]]
            rf_label = classes[preds_rf[idx]]
            mn_label = classes[preds_mn[idx]]

            # Plot Signal
            plt.subplot(2, 2, row_idx*2 + 1)
            plt.plot(signal)
            plt.title(f"{title_prefix}\nTrue: {true_label} | RF: {rf_label} | MN: {mn_label}")
            plt.xlabel("Time (samples)")
            plt.ylabel("Amplitude")

            # Plot Spectrogram
            plt.subplot(2, 2, row_idx*2 + 2)
            # Recompute spec for viz
            sig_float = signal.astype(float)
            sig_float -= np.mean(sig_float)
            S = librosa.feature.melspectrogram(y=sig_float, sr=1000, n_mels=64, n_fft=256, hop_length=16)
            S_dB = librosa.power_to_db(S, ref=np.max)
            librosa.display.specshow(S_dB, sr=1000, hop_length=16, x_axis='time', y_axis='mel')
            plt.colorbar(format='%+2.0f dB')
            plt.title("Spectrogram (What MobileNet Sees)")

        if rf_wins:
            plot_case(rf_wins[0], 0, "Case A: Random Forest Wins (Robust to Noise?)")

        if mn_wins:
            plot_case(mn_wins[0], 1, "Case B: MobileNet Wins (Detects Texture?)")

        plt.tight_layout()
        plt.savefig("viz_disagreement.png")
        print("Saved viz_disagreement.png")

if __name__ == "__main__":
    benchmark_all_models()
