# CNN-LSTM Model for Action Classification

This implementation adds a deep learning approach (CNN-LSTM) for real-time action classification from wearable sensor data, following the professor's suggestion to use a pretrained CNN backbone with LSTM layers for temporal pattern recognition.

## Overview

The CNN-LSTM architecture combines:
1. **1D Convolutional layers** for automatic feature extraction from sensor signals
2. **LSTM layers** for capturing temporal dependencies in motion patterns
3. **Dense layers** for final classification

## Model Performance

### Binary Classification (Walk vs Idle)
- **Test Accuracy**: 97.46%
- **Architecture**: Standard CNN-LSTM (lighter model)
- **Window Size**: 50 timesteps
- **Classes**: walk, idle

### Multiclass Classification (All Actions)
- **Test Accuracy**: 86.98%
- **Architecture**: Deep CNN-LSTM (more complex model)
- **Window Size**: 50 timesteps
- **Classes**: jump, punch, turn_left, turn_right, idle, noise

## Architecture Details

### Standard CNN-LSTM (Binary)
```
Input (50 timesteps × 6 features)
  ↓
Conv1D (64 filters, kernel=5) + BatchNorm + MaxPool + Dropout
  ↓
Conv1D (128 filters, kernel=5) + BatchNorm + MaxPool + Dropout
  ↓
LSTM (64 units, return_sequences=True) + Dropout
  ↓
LSTM (32 units) + Dropout
  ↓
Dense (64 units) + Dropout
  ↓
Dense (num_classes, softmax)
```

### Deep CNN-LSTM (Multiclass)
```
Input (50 timesteps × 6 features)
  ↓
Conv1D (64 filters, kernel=5) + BatchNorm + MaxPool + Dropout
  ↓
Conv1D (128 filters, kernel=5) + BatchNorm + MaxPool + Dropout
  ↓
Conv1D (64 filters, kernel=3) + BatchNorm + Dropout
  ↓
LSTM (128 units, return_sequences=True) + Dropout
  ↓
LSTM (64 units) + Dropout
  ↓
Dense (64 units) + Dropout
  ↓
Dense (num_classes, softmax)
```

## Files

### Training and Models
- **`notebooks/CNN_LSTM_Training.py`**: Training script for CNN-LSTM models
- **`src/cnn_lstm_predictor.py`**: Inference wrapper for real-time predictions
- **`models/cnn_lstm_*.keras`**: Trained model files (not committed, generated during training)
- **`models/cnn_lstm_*_metadata.pkl`**: Model metadata (classes, window size, etc.)
- **`models/cnn_lstm_*_scaler.pkl`**: StandardScaler for normalization

### Integration
- **`src/udp_listener_cnn_lstm.py`**: UDP listener with CNN-LSTM support
  - Set `USE_CNN_LSTM = True` to use CNN-LSTM models
  - Set `USE_CNN_LSTM = False` to use original SVM models

## Usage

### 1. Training Models

```bash
cd /home/runner/work/v3pls/v3pls
python3 notebooks/CNN_LSTM_Training.py
```

This will:
- Load training data from `data/organized_training/`
- Train both binary and multiclass CNN-LSTM models
- Generate confusion matrices and training history plots
- Save models to `models/` directory

### 2. Using Models for Real-time Inference

**Option A: Use the integrated UDP listener**
```python
# In src/udp_listener_cnn_lstm.py, set:
USE_CNN_LSTM = True  # Use CNN-LSTM models
# or
USE_CNN_LSTM = False  # Use original SVM models

# Then run:
python3 src/udp_listener_cnn_lstm.py
```

**Option B: Use the predictor directly**
```python
from cnn_lstm_predictor import CNNLSTMPredictor

# Load model
predictor = CNNLSTMPredictor(
    model_path='models/cnn_lstm_multiclass.keras',
    metadata_path='models/cnn_lstm_multiclass_metadata.pkl',
    scaler_path='models/cnn_lstm_multiclass_scaler.pkl'
)

# Add sensor readings
for reading in sensor_stream:
    predictor.add_reading(reading)
    
    if predictor.is_ready():
        gesture, confidence, probabilities = predictor.predict()
        print(f"Predicted: {gesture} ({confidence:.2%})")
```

## Comparison with SVM

| Aspect | SVM (Original) | CNN-LSTM (New) |
|--------|---------------|----------------|
| **Feature Engineering** | Manual (mean, std, FFT, etc.) | Automatic (learned) |
| **Temporal Modeling** | Sliding window statistics | LSTM sequence modeling |
| **Binary Accuracy** | ~95% | 97.46% |
| **Multiclass Accuracy** | ~85% | 86.98% |
| **Inference Speed** | Faster | Slightly slower |
| **Model Size** | Small (~KB) | Larger (~MB) |
| **Training Time** | Minutes | Minutes to hours |

## Benefits of CNN-LSTM Approach

1. **Automatic Feature Learning**: No need to manually engineer features
2. **Temporal Pattern Recognition**: LSTM captures long-term dependencies
3. **Better Generalization**: Deep learning can learn complex patterns
4. **Scalability**: Easier to add new gestures/actions
5. **Transfer Learning Potential**: Can fine-tune on new data

## Requirements

```
tensorflow>=2.13.0
keras>=2.13.0
numpy
pandas
scikit-learn
joblib
```

## Training Configuration

- **Window Size**: 50 timesteps per sequence
- **Stride**: 10 timesteps (sliding window)
- **Batch Size**: 32
- **Learning Rate**: 0.001 (with ReduceLROnPlateau)
- **Optimizer**: Adam
- **Loss Function**: Categorical Crossentropy
- **Early Stopping**: Patience of 15 epochs
- **Regularization**: Dropout (0.25-0.3), BatchNormalization

## Model Files (Generated)

After training, the following files are created in `models/`:

```
cnn_lstm_binary.keras                          # Binary classifier model
cnn_lstm_binary_metadata.pkl                   # Model configuration
cnn_lstm_binary_scaler.pkl                     # Data normalizer
cnn_lstm_binary_confusion_matrix.png           # Performance visualization
cnn_lstm_binary_training_history.png           # Training curves

cnn_lstm_multiclass.keras                      # Multiclass classifier model
cnn_lstm_multiclass_metadata.pkl               # Model configuration
cnn_lstm_multiclass_scaler.pkl                 # Data normalizer
cnn_lstm_multiclass_confusion_matrix.png       # Performance visualization
cnn_lstm_multiclass_training_history.png       # Training curves
```

## Notes

- Model files (`.keras`, `.pkl`) are excluded from version control via `.gitignore`
- Training generates plots showing model performance
- The CNN-LSTM predictor maintains a buffer of sensor readings for sequence-based inference
- Buffer size matches the window size used during training (50 timesteps)

## Future Improvements

1. **Transfer Learning**: Use pretrained CNN models (e.g., from ImageNet adapted for 1D signals)
2. **Data Augmentation**: Add noise, time warping, or scaling to training data
3. **Attention Mechanism**: Add attention layers to focus on important timesteps
4. **Multi-task Learning**: Train on multiple related tasks simultaneously
5. **Model Compression**: Use quantization or pruning for faster inference
