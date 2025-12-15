import torch
import torch.nn as nn

class CRNN(nn.Module):
    def __init__(self, input_channels=1, num_classes=3):
        super(CRNN, self).__init__()
        # 1. CNN Feature Extractor
        self.cnn = nn.Sequential(
            nn.Conv1d(input_channels, 64, kernel_size=5, stride=1),
            # BatchNorm REMOVED
            # nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Conv1d(64, 128, kernel_size=3, stride=1),
            nn.ReLU(),
            nn.MaxPool1d(2)
        )

        # 2. LSTM Sequence Learner (Standard Unidirectional)
        # Input size is 128 (channels from CNN)
        self.lstm = nn.LSTM(input_size=128, hidden_size=64, num_layers=2, batch_first=True)

        # 3. Classifier
        self.fc = nn.Linear(64, num_classes)

    def forward(self, x):
        # x shape: [Batch, Channels, Time]

        # Run CNN
        x = self.cnn(x)

        # Reshape for LSTM: [Batch, Time, Features]
        x = x.permute(0, 2, 1)

        # Run LSTM
        out, (hn, cn) = self.lstm(x)

        # Take the last hidden state
        x = hn[-1]

        return self.fc(x)
