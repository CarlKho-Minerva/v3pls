import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder
import time

# Add parent directory to path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../data')))
import utils
from max_crnn_model import MaxCRNN

def train_and_evaluate():
    print("--- Model 17: MaxCRNN (Inception + Bi-LSTM + MultiHeadAttention) ---")

    # 1. Load Data
    base_dir = "../data/"
    df = utils.load_and_clean_data(base_dir)

    if df.empty:
        print("No data found. Exiting.")
        return

    # 2. Windowing
    X_raw, y = utils.create_windows(df)

    # 3. Feature Extraction (Set B: Raw Sequence)
    print("Extracting features (Set B)...")
    X_features = utils.extract_features_set_b(X_raw)

    # Reshape for PyTorch: [Batch, Channels, Time]
    X_tensor = torch.tensor(X_features, dtype=torch.float32).unsqueeze(1)

    # Encode labels
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    y_tensor = torch.tensor(y_enc, dtype=torch.long)

    num_classes = len(le.classes_)
    print(f"Classes: {le.classes_}")

    # 4. Split Data
    from sklearn.model_selection import train_test_split
    X_train_np, X_test_np, y_train_np, y_test_np = train_test_split(
        X_features, y_enc, test_size=0.2, stratify=y_enc, random_state=utils.RANDOM_SEED
    )

    # Convert to Tensors (for Test set only, Train set uses Custom Dataset)
    X_test = torch.tensor(X_test_np, dtype=torch.float32).unsqueeze(1)
    y_test = torch.tensor(y_test_np, dtype=torch.long)

    # Custom Dataset with Augmentation
    class EMGDataset(torch.utils.data.Dataset):
        def __init__(self, X, y, augment=False):
            self.X = X
            self.y = y
            self.augment = augment

        def __len__(self):
            return len(self.y)

        def __getitem__(self, idx):
            # X shape: [1000] (raw sequence)
            x = self.X[idx]
            y = self.y[idx]

            if self.augment:
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

            # Convert to tensor and add channel dim: [1, 1000]
            x_tensor = torch.tensor(x, dtype=torch.float32).unsqueeze(0)
            y_tensor = torch.tensor(y, dtype=torch.long)
            return x_tensor, y_tensor

    # Create DataLoaders
    batch_size = 64
    # Train set gets augmentation
    train_dataset = EMGDataset(X_train_np, y_train_np, augment=True)
    # Test set is clean
    test_dataset = TensorDataset(X_test, y_test)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    # 5. Initialize Model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    model = MaxCRNN(input_channels=1, num_classes=num_classes).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.0005) # Lower LR for deeper model

    # 6. Train Loop
    print("Training MaxCRNN (1000 epochs with Early Stopping)...")
    epochs = 1000
    patience = 50
    best_val_loss = float('inf')
    patience_counter = 0
    history = {'accuracy': [], 'loss': [], 'val_loss': [], 'val_accuracy': []}

    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

        epoch_acc = correct / total
        epoch_loss = running_loss / len(train_loader)

        # Validation
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        with torch.no_grad():
            for inputs, labels in test_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                val_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                val_total += labels.size(0)
                val_correct += (predicted == labels).sum().item()

        val_loss /= len(test_loader)
        val_acc = val_correct / val_total

        history['accuracy'].append(epoch_acc)
        history['loss'].append(epoch_loss)
        history['val_loss'].append(val_loss)
        history['val_accuracy'].append(val_acc)

        if (epoch + 1) % 10 == 0:
            print(f"Epoch [{epoch+1}/{epochs}] - Loss: {epoch_loss:.4f} - Acc: {epoch_acc:.4f} - Val Loss: {val_loss:.4f} - Val Acc: {val_acc:.4f}")

        # Checkpoint & Early Stopping
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            torch.save(model.state_dict(), "best_model.pth")
        else:
            patience_counter += 1

        if patience_counter >= patience:
            print(f"Early stopping triggered at epoch {epoch+1}")
            break

    # Load best model
    model.load_state_dict(torch.load("best_model.pth"))
    print("Loaded best model from checkpoint.")

    # 7. Evaluate
    model.eval()
    start_time = time.time()
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            _, predicted = torch.max(outputs.data, 1)
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    inference_time = (time.time() - start_time) / len(X_test) * 1000 # ms per sample

    test_acc = accuracy_score(all_labels, all_preds)
    print(f"Test Accuracy: {test_acc:.4f}")
    print(f"Inference Latency: {inference_time:.4f} ms")

    # 8. Save Model
    torch.save(model.state_dict(), "model.pth")

    # 9. Generate Report
    report = f"""# Model 17: MaxCRNN Results

## Performance
*   **Accuracy:** {test_acc:.4f}
*   **Inference Latency:** {inference_time:.4f} ms
*   **Architecture:** Inception -> Bi-LSTM -> MultiHeadAttention

## Classification Report
```
{classification_report(all_labels, all_preds, target_names=le.classes_)}
```

## Confusion Matrix
```
{confusion_matrix(all_labels, all_preds)}
```
"""

    with open("results.md", "w") as f:
        f.write(report)

    # 10. Visualization
    plt.figure(figsize=(10, 6))
    plt.plot(history['accuracy'], label='Train Acc')
    plt.plot(history['val_accuracy'], label='Val Acc')
    plt.title("MaxCRNN Training History")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.legend()
    plt.savefig("viz_17_maxcrnn.png")
    print("Results and visualization saved.")

if __name__ == "__main__":
    train_and_evaluate()
