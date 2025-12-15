import torch
import torch.nn as nn

class Attention(nn.Module):
    def __init__(self, hidden_size):
        super(Attention, self).__init__()
        self.attention = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, 1)
        )

    def forward(self, hidden_states):
        # hidden_states: [Batch, Time, Hidden]
        attn_weights = self.attention(hidden_states) # [Batch, Time, 1]
        attn_weights = torch.softmax(attn_weights, dim=1)
        # Weighted sum
        context_vector = torch.sum(attn_weights * hidden_states, dim=1) # [Batch, Hidden]
        return context_vector, attn_weights

class CRNN(nn.Module):
    def __init__(self, input_channels=1, num_classes=3):
        super(CRNN, self).__init__()
        # 1. CNN Feature Extractor
        self.cnn = nn.Sequential(
            nn.Conv1d(input_channels, 64, kernel_size=5, stride=1),
            # Removed BatchNorm to preserve amplitude differences
            # nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Dropout(0.3), # Added Dropout

            nn.Conv1d(64, 128, kernel_size=3, stride=1),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Dropout(0.3) # Added Dropout
        )

        # 2. LSTM Sequence Learner (Bidirectional)
        # Input size is 128 (channels from CNN)
        self.lstm = nn.LSTM(input_size=128, hidden_size=64, num_layers=2, batch_first=True, bidirectional=True, dropout=0.3)

        # 3. Attention
        self.attention = Attention(hidden_size=64 * 2) # *2 for bidirectional

        # 4. Classifier
        self.fc = nn.Linear(64 * 2, num_classes)

    def forward(self, x):
        # x shape: [Batch, Channels, Time]
        # Example: [32, 1, 1000]

        # Run CNN
        x = self.cnn(x)
        # Output shape: [Batch, 128, 248]

        # Reshape for LSTM: [Batch, Time, Features]
        x = x.permute(0, 2, 1)
        # Output shape: [Batch, 248, 128]

        # Run LSTM
        # out shape: [Batch, Time, Hidden*2]
        out, (hn, cn) = self.lstm(x)

        # Attention
        x, _ = self.attention(out)
        # Output shape: [Batch, Hidden*2]

        return self.fc(x)
