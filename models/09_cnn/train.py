import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Conv1D, MaxPooling1D, Flatten, GlobalAveragePooling1D
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import time

# Add parent directory to path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../data')))
import utils

def train_and_evaluate():
    print("--- Model 9: 1D Convolutional Neural Network (CNN) ---")

    # 1. Load Data
    base_dir = "../data/"
    df = utils.load_and_clean_data(base_dir)

    # 2. Windowing
    X_raw, y = utils.create_windows(df)

    # 3. Feature Extraction (Set B: Raw Sequence)
    print("Extracting features (Set B)...")
    X_features = utils.extract_features_set_b(X_raw)

    # Reshape for CNN: (samples, time_steps, features)
    X_cnn = X_features.reshape((X_features.shape[0], X_features.shape[1], 1))

    # Encode labels
    from sklearn.preprocessing import LabelEncoder
    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    # 4. Split Data
    X_train, X_test, y_train, y_test = utils.get_data_splits(X_cnn, y_enc)

    # 5. Train
    print("Training 1D CNN...")
    model = Sequential([
        Conv1D(filters=32, kernel_size=3, activation='relu', input_shape=(1000, 1)),
        MaxPooling1D(pool_size=2),
        Conv1D(filters=64, kernel_size=3, activation='relu'),
        MaxPooling1D(pool_size=2),
        # GlobalAveragePooling1D is lighter than Flatten for ESP32
        GlobalAveragePooling1D(),
        Dense(64, activation='relu'),
        Dropout(0.3),
        Dense(3, activation='softmax')
    ])

    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

    history = model.fit(X_train, y_train, epochs=30, batch_size=32, validation_split=0.2, verbose=0)

    # 6. Evaluate
    start_time = time.time()
    y_pred_prob = model.predict(X_test)
    inference_time = (time.time() - start_time) / len(X_test) * 1000 # ms per sample

    y_pred = np.argmax(y_pred_prob, axis=1)

    test_acc = accuracy_score(y_test, y_pred)
    print(f"Test Accuracy: {test_acc:.4f}")
    print(f"Inference Latency: {inference_time:.4f} ms")

    # 7. Save Model
    model.save("model.h5")

    # 8. Generate Report
    report = f"""# Model 9: 1D CNN Results

## Performance
*   **Accuracy:** {test_acc:.4f}
*   **Inference Latency:** {inference_time:.4f} ms
*   **Architecture:** Conv1D(32) -> MaxPool -> Conv1D(64) -> MaxPool -> GAP -> Dense(64) -> Output

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

    # 9. Visualization (Training History)
    plt.figure(figsize=(10, 6))
    plt.plot(history.history['accuracy'], label='Train Acc')
    plt.plot(history.history['val_accuracy'], label='Val Acc')
    plt.title("CNN Training History")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.legend()
    plt.savefig("viz.png")
    print("Results and visualization saved.")

if __name__ == "__main__":
    train_and_evaluate()
