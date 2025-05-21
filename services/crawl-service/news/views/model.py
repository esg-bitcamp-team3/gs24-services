# e_model.py

import torch.nn as nn

class ESG_CNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv1d( in_channels=2, out_channels=32, kernel_size=3, padding=1)
        self.bn1   = nn.BatchNorm1d(32)
        self.relu  = nn.ReLU()
        self.conv2 = nn.Conv1d(32, 64, kernel_size=3, padding=1)
        self.bn2   = nn.BatchNorm1d(64)
        self.global_pool = nn.AdaptiveMaxPool1d(1)
        self.fc    = nn.Linear(64, 6)

    def forward(self, x):
        # x: [B,12,2] → [B,2,12]
        x = x.permute(0,2,1)
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.relu(self.bn2(self.conv2(x)))
        x = self.global_pool(x).squeeze(-1)  # [B,64]
        return self.fc(x)
