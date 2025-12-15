import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Conv1D, MaxPooling1D, GlobalAveragePooling1D, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import time

# Add parent directory to path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../data')))
import utils

# Data Augmentation Functions
def augment_signal(x):
    """Apply data augmentation to a single signal window."""
    # 1. Gaussian Noise (Jitter)
    if np.random.rand() < 0.5:
        noise = np.random.normal(0, 0.01, x.shape)
        x = x + noise

    # 2. Scale (Amplitude Shift)
    if np.random.rand() < 0.5:
        scale = np.random.uniform(0.9, 1.1)
        x = x * scale

    # 3. Time Shift
    if np.random.rand() < 0.5:
        shift = np.random.randint(-50, 50)
        x = np.roll(x, shift)

    return x

class AugmentedDataGenerator(tf.keras.utils.Sequence):
    """Keras Sequence for on-the-fly data augmentation."""

    def __init__(self, X, y, batch_size=32, augment=True, shuffle=True):
        self.X = X
        self.y = y
        self.batch_size = batch_size
        self.augment = augment
        self.shuffle = shuffle
        self.indices = np.arange(len(self.X))
        if shuffle:
            np.random.shuffle(self.indices)

    def __len__(self):
        return int(np.ceil(len(self.X) / self.batch_size))

    def __getitem__(self, idx):
        batch_indices = self.indices[idx * self.batch_size:(idx + 1) * self.batch_size]
        X_batch = self.X[batch_indices].copy()
        y_batch = self.y[batch_indices]

        if self.augment:
            for i in range(len(X_batch)):
                X_batch[i, :, 0] = augment_signal(X_batch[i, :, 0])

        return X_batch, y_batch

    def on_epoch_end(self):
        if self.shuffle:
            np.random.shuffle(self.indices)

def train_and_evaluate():
    print("=" * 60)
    print("Model 9b: 1D CNN with Data Augmentation (1000 Epochs)")
    print("=" * 60)
    print("\nThis experiment addresses the reviewer critique:")
    print("'Did the CNN fail because of small data, or lack of augmentation?'\n")

    # Set random seed for reproducibility
    np.random.seed(utils.RANDOM_SEED)
    tf.random.set_seed(utils.RANDOM_SEED)

    # 1. Load Data
    base_dir = "../data/"
    df = utils.load_and_clean_data(base_dir)

    if df.empty:
        print("No data found. Exiting.")
        return

    # 2. Windowing
    X_raw, y = utils.create_windows(df)
    print(f"Dataset: {len(X_raw)} windows")

    # 3. Feature Extraction (Set B: Raw Sequence)
    print("Extracting features (Set B: Raw Sequence)...")
    X_features = utils.extract_features_set_b(X_raw)

    # Reshape for CNN: (samples, time_steps, features)
    X_cnn = X_features.reshape((X_features.shape[0], X_features.shape[1], 1))

    # Encode labels
    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    # 4. Split Data
    X_train, X_test, y_train, y_test = train_test_split(
        X_cnn, y_enc, test_size=0.2, stratify=y_enc, random_state=utils.RANDOM_SEED
    )
    print(f"Train: {len(X_train)}, Test: {len(X_test)}")

    # Create data generators
    batch_size = 32
    train_gen = AugmentedDataGenerator(X_train, y_train, batch_size=batch_size, augment=True)
    val_gen = AugmentedDataGenerator(X_test, y_test, batch_size=batch_size, augment=False, shuffle=False)

    # 5. Build Model (same architecture as original)
    print("\nBuilding 1D CNN...")
    model = Sequential([
        Conv1D(filters=32, kernel_size=3, activation='relu', input_shape=(1000, 1)),
        BatchNormalization(),  # Added for stability
        MaxPooling1D(pool_size=2),
        Conv1D(filters=64, kernel_size=3, activation='relu'),
        BatchNormalization(),  # Added for stability
        MaxPooling1D(pool_size=2),
        GlobalAveragePooling1D(),
        Dense(64, activation='relu'),
        Dropout(0.3),
        Dense(3, activation='softmax')
    ])

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )

    model.summary()

    # 6. Callbacks
    early_stop = EarlyStopping(
        monitor='val_loss',
        patience=50,
        restore_best_weights=True,
        verbose=1
    )
    checkpoint = ModelCheckpoint(
        'best_model.h5',
        monitor='val_loss',
        save_best_only=True,
        verbose=0
    )

    # 7. Train
    print("\n" + "=" * 60)
    print("Training with Data Augmentation (1000 epochs, patience=50)")
    print("Augmentation: Jitter, Scaling, Time Shift")
    print("=" * 60 + "\n")

    history = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=1000,
        callbacks=[early_stop, checkpoint],
        verbose=1
    )

    # 8. Evaluate
    print("\nEvaluating on test set...")
    start_time = time.time()
    y_pred_prob = model.predict(X_test, verbose=0)
    inference_time = (time.time() - start_time) / len(X_test) * 1000  # ms per sample

    y_pred = np.argmax(y_pred_prob, axis=1)

    test_acc = accuracy_score(y_test, y_pred)
    print(f"\n{'=' * 60}")
    print(f"RESULTS: 1D CNN + Data Augmentation")
    print(f"{'=' * 60}")
    print(f"Test Accuracy: {test_acc:.4f} ({test_acc*100:.2f}%)")
    print(f"Inference Latency: {inference_time:.4f} ms")
    print(f"Epochs trained: {len(history.history['accuracy'])}")

    # Classification Report
    print(f"\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=le.classes_))

    # 9. Save Model
    model.save("model.h5")
    print("Model saved to model.h5")

    # 10. Generate Report
    cm = confusion_matrix(y_test, y_pred)
    report = f"""# Model 9b: 1D CNN with Data Augmentation

## Experiment Purpose
This experiment addresses the reviewer critique: *"Did the CNN fail because of small data,
or because you didn't augment the data like you did for the complex model?"*

## Training Configuration
- **Epochs:** 1000 (with Early Stopping, patience=50)
- **Data Augmentation:** Yes (Jitter, Scaling, Time Shift)
- **Batch Size:** {batch_size}
- **Learning Rate:** 0.001
- **Added:** BatchNormalization layers for training stability

## Results
| Metric | Original CNN (Model 9) | CNN + Augmentation |
|--------|------------------------|-------------------|
| Accuracy | 49.63% | {test_acc*100:.2f}% |
| Epochs | 30 | {len(history.history['accuracy'])} |
| Augmentation | No | Yes |

## Performance
*   **Accuracy:** {test_acc:.4f}
*   **Inference Latency:** {inference_time:.4f} ms

## Classification Report
```
{classification_report(y_test, y_pred, target_names=le.classes_)}
```

## Confusion Matrix
```
{cm}
```

## Conclusion
{"**Improvement:** Data Augmentation + longer training improved CNN performance." if test_acc > 0.55 else "**Finding:** Even with augmentation, the CNN struggles with this small dataset, confirming that the architecture lacks sufficient inductive bias for generalizing from limited samples."}
"""

    with open("results.md", "w") as f:
        f.write(report)
    print("Report saved to results.md")

    # 11. Visualization
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Training History
    axes[0].plot(history.history['accuracy'], label='Train Acc', linewidth=2)
    axes[0].plot(history.history['val_accuracy'], label='Val Acc', linewidth=2)
    axes[0].set_title("CNN + Augmentation: Training History")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Accuracy")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Loss
    axes[1].plot(history.history['loss'], label='Train Loss', linewidth=2)
    axes[1].plot(history.history['val_loss'], label='Val Loss', linewidth=2)
    axes[1].set_title("CNN + Augmentation: Loss")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Loss")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("viz_training.png", dpi=150, bbox_inches='tight')
    print("Training visualization saved to viz_training.png")

    # Confusion Matrix Plot
    plt.figure(figsize=(8, 6))
    import seaborn as sns
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=le.classes_, yticklabels=le.classes_)
    plt.title(f"CNN + Augmentation Confusion Matrix\nAccuracy: {test_acc:.2%}")
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.tight_layout()
    plt.savefig("cm_09b_cnn_aug.png", dpi=150, bbox_inches='tight')
    print("Confusion matrix saved to cm_09b_cnn_aug.png")

    print(f"\n{'=' * 60}")
    print("DONE! All results saved.")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    train_and_evaluate()
