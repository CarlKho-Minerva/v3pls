#!/usr/bin/env python3
"""
CNN-LSTM Model Inference Wrapper

This module provides a wrapper class for using the trained CNN-LSTM model
for real-time inference in the UDP listener dashboard.
"""

import numpy as np
import joblib
from pathlib import Path
from collections import deque
import tensorflow as tf
from tensorflow import keras


class CNNLSTMPredictor:
    """
    Wrapper for CNN-LSTM model inference.
    
    This class handles:
    - Model loading
    - Buffer management for sequence data
    - Real-time prediction with confidence scores
    """
    
    def __init__(self, model_path, metadata_path, scaler_path):
        """
        Initialize the CNN-LSTM predictor.
        
        Args:
            model_path: Path to the trained Keras model (.keras file)
            metadata_path: Path to the metadata pickle file
            scaler_path: Path to the StandardScaler pickle file
        """
        print(f"Loading CNN-LSTM model from {model_path}...")
        
        # Load model
        self.model = keras.models.load_model(model_path)
        
        # Load metadata
        self.metadata = joblib.load(metadata_path)
        self.classes = self.metadata['classes']
        self.window_size = self.metadata['window_size']
        self.num_features = self.metadata['num_features']
        
        # Load scaler
        self.scaler = joblib.load(scaler_path)
        
        # Initialize buffer for sequence data
        self.buffer = deque(maxlen=self.window_size)
        
        print(f"✅ Model loaded successfully")
        print(f"  Classes: {self.classes}")
        print(f"  Window size: {self.window_size}")
        print(f"  Features: {self.num_features}")
    
    def add_reading(self, reading):
        """
        Add a sensor reading to the buffer.
        
        Args:
            reading: Dictionary with sensor data (accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z)
        """
        # Extract features in expected order
        feature_vector = [
            reading.get('accel_x', 0),
            reading.get('accel_y', 0),
            reading.get('accel_z', 0),
            reading.get('gyro_x', 0),
            reading.get('gyro_y', 0),
            reading.get('gyro_z', 0)
        ]
        self.buffer.append(feature_vector)
    
    def predict(self):
        """
        Make a prediction based on the current buffer.
        
        Returns:
            tuple: (predicted_class, confidence, all_probabilities)
                   Returns (None, 0.0, None) if buffer is not full
        """
        if len(self.buffer) < self.window_size:
            return None, 0.0, None
        
        # Convert buffer to numpy array
        sequence = np.array(list(self.buffer)).reshape(1, self.window_size, self.num_features)
        
        # Normalize using the scaler
        # Reshape for scaling
        sequence_2d = sequence.reshape(-1, self.num_features)
        sequence_scaled_2d = self.scaler.transform(sequence_2d)
        sequence_scaled = sequence_scaled_2d.reshape(1, self.window_size, self.num_features)
        
        # Predict
        probabilities = self.model.predict(sequence_scaled, verbose=0)[0]
        
        # Get prediction
        predicted_idx = np.argmax(probabilities)
        predicted_class = self.classes[predicted_idx]
        confidence = probabilities[predicted_idx]
        
        return predicted_class, float(confidence), probabilities
    
    def reset_buffer(self):
        """Clear the buffer."""
        self.buffer.clear()
    
    def get_buffer_size(self):
        """Get current buffer size."""
        return len(self.buffer)
    
    def is_ready(self):
        """Check if buffer is full and ready for prediction."""
        return len(self.buffer) == self.window_size


def load_cnn_lstm_models(models_dir):
    """
    Load both binary and multiclass CNN-LSTM models.
    
    Args:
        models_dir: Path to models directory
    
    Returns:
        tuple: (binary_predictor, multiclass_predictor)
               Returns (None, None) if models don't exist
    """
    models_path = Path(models_dir)
    
    binary_model_path = models_path / "cnn_lstm_binary.keras"
    binary_metadata_path = models_path / "cnn_lstm_binary_metadata.pkl"
    binary_scaler_path = models_path / "cnn_lstm_binary_scaler.pkl"
    
    multi_model_path = models_path / "cnn_lstm_multiclass.keras"
    multi_metadata_path = models_path / "cnn_lstm_multiclass_metadata.pkl"
    multi_scaler_path = models_path / "cnn_lstm_multiclass_scaler.pkl"
    
    binary_predictor = None
    multi_predictor = None
    
    # Load binary model if it exists
    if binary_model_path.exists() and binary_metadata_path.exists() and binary_scaler_path.exists():
        try:
            binary_predictor = CNNLSTMPredictor(
                binary_model_path,
                binary_metadata_path,
                binary_scaler_path
            )
        except Exception as e:
            print(f"⚠️ Failed to load binary CNN-LSTM model: {e}")
    
    # Load multiclass model if it exists
    if multi_model_path.exists() and multi_metadata_path.exists() and multi_scaler_path.exists():
        try:
            multi_predictor = CNNLSTMPredictor(
                multi_model_path,
                multi_metadata_path,
                multi_scaler_path
            )
        except Exception as e:
            print(f"⚠️ Failed to load multiclass CNN-LSTM model: {e}")
    
    return binary_predictor, multi_predictor


if __name__ == "__main__":
    # Test loading
    from pathlib import Path
    
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    MODELS_DIR = PROJECT_ROOT / "models"
    
    print("Testing CNN-LSTM model loading...")
    binary_pred, multi_pred = load_cnn_lstm_models(MODELS_DIR)
    
    if binary_pred:
        print("\n✅ Binary model loaded successfully")
    else:
        print("\n❌ Binary model not found")
    
    if multi_pred:
        print("✅ Multiclass model loaded successfully")
    else:
        print("❌ Multiclass model not found")
    
    # Test inference with dummy data
    if multi_pred:
        print("\n🧪 Testing inference with dummy data...")
        for i in range(60):  # Fill buffer and predict
            dummy_reading = {
                'accel_x': np.random.randn(),
                'accel_y': np.random.randn(),
                'accel_z': np.random.randn(),
                'gyro_x': np.random.randn(),
                'gyro_y': np.random.randn(),
                'gyro_z': np.random.randn()
            }
            multi_pred.add_reading(dummy_reading)
            
            if multi_pred.is_ready():
                pred_class, confidence, probs = multi_pred.predict()
                print(f"Prediction: {pred_class} (confidence: {confidence:.2%})")
                break
