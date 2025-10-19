#!/usr/bin/env python3
"""
CNN-LSTM Model Training for Action Classification

This script implements a CNN-LSTM architecture for time-series action recognition:
1. 1D CNN layers for feature extraction from sensor data
2. LSTM layers for temporal pattern recognition
3. Dense layers for classification

The approach follows the professor's suggestion of using a CNN backbone
for feature extraction, followed by LSTM for sequence modeling.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns

# TensorFlow/Keras imports
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models, callbacks
from tensorflow.keras.utils import to_categorical


def load_sequence_data(data_dir, classes, window_size=50, stride=10):
    """
    Load time-series data as sequences for CNN-LSTM model.
    
    Args:
        data_dir: Path to data directory
        classes: List of class names
        window_size: Number of timesteps per sequence
        stride: Step size for sliding window
    
    Returns:
        X: Array of sequences (samples, timesteps, features)
        y: Array of labels
    """
    X_sequences = []
    y_labels = []
    data_path = Path(data_dir)
    
    for class_idx, class_name in enumerate(classes):
        class_path = data_path / class_name
        if not class_path.exists():
            print(f"Warning: {class_path} does not exist")
            continue
        
        file_count = 0
        for file_path in class_path.glob("*.csv"):
            df = pd.read_csv(file_path)
            
            # Select sensor columns
            sensor_cols = ['accel_x', 'accel_y', 'accel_z', 'gyro_x', 'gyro_y', 'gyro_z']
            available_cols = [col for col in sensor_cols if col in df.columns]
            
            if len(available_cols) == 0:
                continue
            
            sensor_data = df[available_cols].values
            
            # Create sliding windows
            for i in range(0, len(sensor_data) - window_size + 1, stride):
                window = sensor_data[i:i + window_size]
                if len(window) == window_size:
                    X_sequences.append(window)
                    y_labels.append(class_idx)
            
            file_count += 1
        
        print(f"  - {class_name}: {file_count} files processed")
    
    X = np.array(X_sequences)
    y = np.array(y_labels)
    
    print(f"\nLoaded {len(X)} sequences with shape {X.shape}")
    return X, y


def create_cnn_lstm_model(input_shape, num_classes, model_type='standard'):
    """
    Create CNN-LSTM model for time-series classification.
    
    Args:
        input_shape: (timesteps, features)
        num_classes: Number of output classes
        model_type: 'standard' or 'deep' for different architectures
    
    Returns:
        Compiled Keras model
    """
    model = models.Sequential(name='CNN_LSTM_Classifier')
    
    # Input layer
    model.add(layers.Input(shape=input_shape))
    
    if model_type == 'deep':
        # Deeper CNN for better feature extraction
        model.add(layers.Conv1D(64, kernel_size=5, activation='relu', padding='same'))
        model.add(layers.BatchNormalization())
        model.add(layers.MaxPooling1D(pool_size=2))
        model.add(layers.Dropout(0.3))
        
        model.add(layers.Conv1D(128, kernel_size=5, activation='relu', padding='same'))
        model.add(layers.BatchNormalization())
        model.add(layers.MaxPooling1D(pool_size=2))
        model.add(layers.Dropout(0.3))
        
        model.add(layers.Conv1D(64, kernel_size=3, activation='relu', padding='same'))
        model.add(layers.BatchNormalization())
        model.add(layers.Dropout(0.3))
        
        # LSTM layers
        model.add(layers.LSTM(128, return_sequences=True))
        model.add(layers.Dropout(0.3))
        model.add(layers.LSTM(64))
        model.add(layers.Dropout(0.3))
    else:
        # Standard CNN-LSTM architecture
        # Conv1D layers for local feature extraction
        model.add(layers.Conv1D(64, kernel_size=5, activation='relu', padding='same'))
        model.add(layers.BatchNormalization())
        model.add(layers.MaxPooling1D(pool_size=2))
        model.add(layers.Dropout(0.25))
        
        model.add(layers.Conv1D(128, kernel_size=5, activation='relu', padding='same'))
        model.add(layers.BatchNormalization())
        model.add(layers.MaxPooling1D(pool_size=2))
        model.add(layers.Dropout(0.25))
        
        # LSTM layers for temporal dependencies
        model.add(layers.LSTM(64, return_sequences=True))
        model.add(layers.Dropout(0.25))
        model.add(layers.LSTM(32))
        model.add(layers.Dropout(0.25))
    
    # Dense layers for classification
    model.add(layers.Dense(64, activation='relu'))
    model.add(layers.Dropout(0.3))
    model.add(layers.Dense(num_classes, activation='softmax'))
    
    # Compile model
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    return model


def normalize_sequences(X_train, X_test):
    """
    Normalize sequences using StandardScaler per feature.
    
    Args:
        X_train: Training sequences (samples, timesteps, features)
        X_test: Test sequences (samples, timesteps, features)
    
    Returns:
        Normalized X_train, X_test, and the scaler
    """
    # Reshape to 2D for scaling
    n_samples_train, n_timesteps, n_features = X_train.shape
    n_samples_test = X_test.shape[0]
    
    X_train_2d = X_train.reshape(-1, n_features)
    X_test_2d = X_test.reshape(-1, n_features)
    
    # Fit scaler on training data
    scaler = StandardScaler()
    X_train_scaled_2d = scaler.fit_transform(X_train_2d)
    X_test_scaled_2d = scaler.transform(X_test_2d)
    
    # Reshape back to 3D
    X_train_scaled = X_train_scaled_2d.reshape(n_samples_train, n_timesteps, n_features)
    X_test_scaled = X_test_scaled_2d.reshape(n_samples_test, n_timesteps, n_features)
    
    return X_train_scaled, X_test_scaled, scaler


def plot_training_history(history, save_path):
    """Plot training history."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Accuracy
    axes[0].plot(history.history['accuracy'], label='Train Accuracy')
    axes[0].plot(history.history['val_accuracy'], label='Val Accuracy')
    axes[0].set_title('Model Accuracy')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Accuracy')
    axes[0].legend()
    axes[0].grid(True)
    
    # Loss
    axes[1].plot(history.history['loss'], label='Train Loss')
    axes[1].plot(history.history['val_loss'], label='Val Loss')
    axes[1].set_title('Model Loss')
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('Loss')
    axes[1].legend()
    axes[1].grid(True)
    
    plt.tight_layout()
    plt.savefig(save_path)
    print(f"Training history plot saved to {save_path}")


def train_and_evaluate(X, y, classes, model_name, models_dir, window_size, model_type='standard'):
    """
    Train and evaluate CNN-LSTM model.
    
    Args:
        X: Input sequences
        y: Labels
        classes: Class names
        model_name: Name for saving the model
        models_dir: Directory to save models
        window_size: Sequence length
        model_type: Type of model architecture
    """
    print(f"\n{'='*20} Training CNN-LSTM {model_name} Classifier {'='*20}")
    
    if len(np.unique(y)) < 2:
        print(f"Skipping training for {model_name}: only one class present.")
        return
    
    # Print dataset statistics
    unique, counts = np.unique(y, return_counts=True)
    print(f"\nDataset: {len(X)} sequences")
    print(f"Sequence shape: {X.shape}")
    for cls_idx, count in zip(unique, counts):
        print(f"  - {classes[cls_idx]}: {count} sequences")
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\nTrain set: {len(X_train)} sequences")
    print(f"Test set: {len(X_test)} sequences")
    
    # Normalize data
    X_train_norm, X_test_norm, scaler = normalize_sequences(X_train, X_test)
    
    # Convert labels to categorical
    y_train_cat = to_categorical(y_train, num_classes=len(classes))
    y_test_cat = to_categorical(y_test, num_classes=len(classes))
    
    # Create model
    input_shape = (X_train_norm.shape[1], X_train_norm.shape[2])
    model = create_cnn_lstm_model(input_shape, len(classes), model_type=model_type)
    
    print("\nModel Architecture:")
    model.summary()
    
    # Callbacks
    models_path = Path(models_dir)
    models_path.mkdir(exist_ok=True)
    
    checkpoint_path = models_path / f"cnn_lstm_{model_name}_best.keras"
    callbacks_list = [
        callbacks.EarlyStopping(
            monitor='val_loss',
            patience=15,
            restore_best_weights=True,
            verbose=1
        ),
        callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=0.00001,
            verbose=1
        ),
        callbacks.ModelCheckpoint(
            checkpoint_path,
            monitor='val_accuracy',
            save_best_only=True,
            verbose=1
        )
    ]
    
    # Train model
    print("\n🚀 Training model...")
    history = model.fit(
        X_train_norm, y_train_cat,
        validation_data=(X_test_norm, y_test_cat),
        epochs=100,
        batch_size=32,
        callbacks=callbacks_list,
        verbose=1
    )
    
    # Plot training history
    plot_training_history(
        history,
        models_path / f"cnn_lstm_{model_name}_training_history.png"
    )
    
    # Evaluate on test set
    print("\n📈 Evaluating on test set...")
    test_loss, test_acc = model.evaluate(X_test_norm, y_test_cat, verbose=0)
    print(f"Test Accuracy: {test_acc:.4f}")
    print(f"Test Loss: {test_loss:.4f}")
    
    # Predictions
    y_pred_probs = model.predict(X_test_norm, verbose=0)
    y_pred = np.argmax(y_pred_probs, axis=1)
    
    # Classification report
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=classes, zero_division=0))
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        cm, annot=True, fmt='d', cmap='Blues',
        xticklabels=classes, yticklabels=classes
    )
    plt.title(f'Confusion Matrix - CNN-LSTM {model_name.capitalize()}')
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.tight_layout()
    cm_path = models_path / f"cnn_lstm_{model_name}_confusion_matrix.png"
    plt.savefig(cm_path)
    print(f"Confusion matrix saved to {cm_path}")
    
    # Save model and metadata
    print("\n💾 Saving model and metadata...")
    model.save(models_path / f"cnn_lstm_{model_name}.keras")
    
    # Save metadata
    metadata = {
        'classes': classes,
        'window_size': window_size,
        'input_shape': input_shape,
        'num_features': X_train_norm.shape[2],
        'test_accuracy': float(test_acc),
        'model_type': model_type
    }
    joblib.dump(metadata, models_path / f"cnn_lstm_{model_name}_metadata.pkl")
    joblib.dump(scaler, models_path / f"cnn_lstm_{model_name}_scaler.pkl")
    
    print(f"✅ Model saved to {models_path / f'cnn_lstm_{model_name}.keras'}")
    print(f"✅ Metadata saved to {models_path / f'cnn_lstm_{model_name}_metadata.pkl'}")
    print(f"✅ Scaler saved to {models_path / f'cnn_lstm_{model_name}_scaler.pkl'}")


def main():
    """Main training function."""
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    ORGANIZED_DATA_DIR = PROJECT_ROOT / "data" / "organized_training"
    MODELS_DIR = PROJECT_ROOT / "models"
    
    # Set random seeds for reproducibility
    np.random.seed(42)
    tf.random.set_seed(42)
    
    # Configuration
    WINDOW_SIZE = 50  # Number of timesteps per sequence
    STRIDE = 10  # Sliding window stride
    
    print("="*60)
    print("CNN-LSTM Model Training for Action Classification")
    print("="*60)
    print(f"Window Size: {WINDOW_SIZE}")
    print(f"Stride: {STRIDE}")
    
    # Binary classification: walk vs idle
    print("\n" + "="*60)
    print("BINARY CLASSIFICATION (Walk vs Idle)")
    print("="*60)
    binary_classes = ['walk', 'idle']
    X_binary, y_binary = load_sequence_data(
        ORGANIZED_DATA_DIR / "binary_classification",
        binary_classes,
        window_size=WINDOW_SIZE,
        stride=STRIDE
    )
    
    if X_binary.size > 0 and len(np.unique(y_binary)) > 1:
        train_and_evaluate(
            X_binary, y_binary, binary_classes,
            'binary', MODELS_DIR, WINDOW_SIZE, model_type='standard'
        )
    else:
        print("Insufficient data for binary classification")
    
    # Multiclass classification: all actions
    print("\n" + "="*60)
    print("MULTICLASS CLASSIFICATION (All Actions)")
    print("="*60)
    multi_classes = ['jump', 'punch', 'turn_left', 'turn_right', 'idle', 'noise']
    X_multi, y_multi = load_sequence_data(
        ORGANIZED_DATA_DIR / "multiclass_classification",
        multi_classes,
        window_size=WINDOW_SIZE,
        stride=STRIDE
    )
    
    if X_multi.size > 0 and len(np.unique(y_multi)) > 1:
        train_and_evaluate(
            X_multi, y_multi, multi_classes,
            'multiclass', MODELS_DIR, WINDOW_SIZE, model_type='deep'
        )
    else:
        print("Insufficient data for multiclass classification")
    
    print("\n" + "="*60)
    print("✅ Training Complete!")
    print("="*60)


if __name__ == "__main__":
    main()
