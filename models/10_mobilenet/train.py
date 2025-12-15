import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Dense, Dropout, GlobalAveragePooling2D, Input
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import time
import cv2

# Add parent directory to path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../data')))
import utils

def train_and_evaluate():
    print("--- Model 10: Transfer Learning (MobileNetV2) ---")

    # 1. Load Data
    base_dir = "../data/"
    df = utils.load_and_clean_data(base_dir)

    # 2. Windowing
    X_raw, y = utils.create_windows(df)

    # 3. Feature Extraction (Set C: Spectrograms)
    print("Extracting features (Set C: Spectrograms)...")
    # This returns (N, 64, 63) or similar depending on n_fft/hop_length
    X_specs = utils.extract_features_set_c(X_raw)
    print(f"Spectrogram Shape: {X_specs.shape}")

    # 4. Preprocessing for MobileNetV2
    # MobileNet expects (224, 224, 3) or at least (32, 32, 3)
    # We need to resize and replicate channels
    print("Resizing spectrograms for MobileNetV2...")

    def preprocess_specs(specs):
        processed = []
        for spec in specs:
            # Resize to 96x96 (supported by MobileNetV2 and lighter than 224)
            # spec is (64, 63)
            resized = cv2.resize(spec, (96, 96))

            # Normalize to [-1, 1] as required by MobileNetV2
            # Librosa dB is roughly -80 to 0. Let's normalize min-max to 0-255 then preprocess
            norm = (resized - resized.min()) / (resized.max() - resized.min()) * 255
            norm = norm.astype(np.uint8)

            # Convert to RGB (3 channels)
            rgb = cv2.cvtColor(norm, cv2.COLOR_GRAY2RGB)

            # MobileNetV2 preprocess (expects float -1 to 1)
            pre = preprocess_input(rgb.astype(np.float32))
            processed.append(pre)

        return np.array(processed)

    X_mobile = preprocess_specs(X_specs)
    print(f"Input Shape: {X_mobile.shape}")

    # Encode labels
    from sklearn.preprocessing import LabelEncoder
    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    # 5. Split Data
    X_train, X_test, y_train, y_test = utils.get_data_splits(X_mobile, y_enc)

    # 6. Train
    print("Loading MobileNetV2...")
    base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(96, 96, 3))

    # Freeze base model
    base_model.trainable = False

    # Add custom head
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(128, activation='relu')(x)
    x = Dropout(0.3)(x)
    predictions = Dense(3, activation='softmax')(x)

    model = Model(inputs=base_model.input, outputs=predictions)

    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

    print("Training (Fine-tuning)...")
    history = model.fit(X_train, y_train, epochs=20, batch_size=32, validation_split=0.2, verbose=0)

    # 7. Evaluate
    start_time = time.time()
    y_pred_prob = model.predict(X_test)
    inference_time = (time.time() - start_time) / len(X_test) * 1000 # ms per sample

    y_pred = np.argmax(y_pred_prob, axis=1)

    test_acc = accuracy_score(y_test, y_pred)
    print(f"Test Accuracy: {test_acc:.4f}")
    print(f"Inference Latency: {inference_time:.4f} ms")

    # 8. Save Model
    model.save("model.h5")

    # 9. Generate Report
    report = f"""# Model 10: MobileNetV2 Results

## Performance
*   **Accuracy:** {test_acc:.4f}
*   **Inference Latency:** {inference_time:.4f} ms
*   **Input Size:** 96x96x3
*   **Base:** MobileNetV2 (ImageNet)

## Classification Report
```
{classification_report(y_test, y_pred, target_names=le.classes_)}
```

## Confusion Matrix
```
{confusion_matrix(y_test, y_pred)}
```
"""

    with open("results.md", "w") as f:
        f.write(report)

    # 10. Visualization (Training History)
    plt.figure(figsize=(10, 6))
    plt.plot(history.history['accuracy'], label='Train Acc')
    plt.plot(history.history['val_accuracy'], label='Val Acc')
    plt.title("MobileNetV2 Training History")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.legend()
    plt.savefig("viz.png")
    print("Results and visualization saved.")

if __name__ == "__main__":
    train_and_evaluate()
