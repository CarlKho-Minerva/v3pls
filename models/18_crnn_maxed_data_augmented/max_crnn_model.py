import torch
import torch.nn as nn
import torch.nn.functional as F

class InceptionBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(InceptionBlock, self).__init__()

        # Bottleneck to reduce dimensions before expensive convs
        bottleneck_channels = out_channels // 4

        # Branch 1: 1x1 Conv (Bottleneck) -> 3x1 Conv
        self.branch1 = nn.Sequential(
            nn.Conv1d(in_channels, bottleneck_channels, kernel_size=1),
            nn.BatchNorm1d(bottleneck_channels),
            nn.ReLU(),
            nn.Conv1d(bottleneck_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm1d(out_channels),
            nn.ReLU()
        )

        # Branch 2: 1x1 Conv (Bottleneck) -> 5x1 Conv
        self.branch2 = nn.Sequential(
            nn.Conv1d(in_channels, bottleneck_channels, kernel_size=1),
            nn.BatchNorm1d(bottleneck_channels),
            nn.ReLU(),
            nn.Conv1d(bottleneck_channels, out_channels, kernel_size=5, padding=2),
            nn.BatchNorm1d(out_channels),
            nn.ReLU()
        )

        # Branch 3: 1x1 Conv (Bottleneck) -> 11x1 Conv (Longer receptive field)
        self.branch3 = nn.Sequential(
            nn.Conv1d(in_channels, bottleneck_channels, kernel_size=1),
            nn.BatchNorm1d(bottleneck_channels),
            nn.ReLU(),
            nn.Conv1d(bottleneck_channels, out_channels, kernel_size=11, padding=5),
            nn.BatchNorm1d(out_channels),
            nn.ReLU()
        )

        # Branch 4: MaxPool -> 1x1 Conv
        self.branch4 = nn.Sequential(
            nn.MaxPool1d(kernel_size=3, stride=1, padding=1),
            nn.Conv1d(in_channels, out_channels, kernel_size=1),
            nn.BatchNorm1d(out_channels),
            nn.ReLU()
        )

    def forward(self, x):
        b1 = self.branch1(x)
        b2 = self.branch2(x)
        b3 = self.branch3(x)
        b4 = self.branch4(x)
        return torch.cat([b1, b2, b3, b4], dim=1)

class MaxCRNN(nn.Module):
    def __init__(self, input_channels=1, num_classes=3):
        super(MaxCRNN, self).__init__()

        # 1. Inception Feature Extractor
        # Input: [Batch, 1, 1000]
        self.inception1 = InceptionBlock(input_channels, 32) # Output channels: 32*4 = 128
        self.pool1 = nn.MaxPool1d(2)
        self.dropout1 = nn.Dropout(0.3)

        self.inception2 = InceptionBlock(128, 64) # Output channels: 64*4 = 256
        self.pool2 = nn.MaxPool1d(2)
        self.dropout2 = nn.Dropout(0.3)

        # 2. Bi-LSTM Sequence Learner
        # Input size: 256 (from Inception2)
        self.lstm = nn.LSTM(input_size=256, hidden_size=128, num_layers=2, batch_first=True, bidirectional=True, dropout=0.3)

        # 3. Multi-Head Attention
        # Input: [Batch, Time, Hidden*2] -> [Batch, Time, 256]
        self.attention = nn.MultiheadAttention(embed_dim=256, num_heads=8, batch_first=True)

        # 4. Classifier
        self.fc = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.4),
            nn.Linear(128, num_classes)
        )

    def forward(self, x):
        # x: [Batch, 1, 1000]

        # Inception Blocks
        x = self.inception1(x)
        x = self.pool1(x)
        x = self.dropout1(x)

        x = self.inception2(x)
        x = self.pool2(x)
        x = self.dropout2(x)
        # x shape: [Batch, 256, 250] (approx)

        # Reshape for LSTM: [Batch, Time, Features]
        x = x.permute(0, 2, 1)

        # LSTM
        # out: [Batch, Time, 256]
        out, _ = self.lstm(x)

        # Multi-Head Attention
        # Query, Key, Value are all 'out' (Self-Attention)
        attn_out, _ = self.attention(out, out, out)

        # Global Average Pooling over time (or take last state, but GAP is better with Attention)
        # attn_out: [Batch, Time, 256]
        x = torch.mean(attn_out, dim=1) # [Batch, 256]

        return self.fc(x)
