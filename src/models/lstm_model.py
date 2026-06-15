import logging

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler

from src.config import config
from src.models.base import BaseModel

logger = logging.getLogger(__name__)


class _LSTMModule(nn.Module):
    def __init__(self, input_size=1, hidden_size=32, num_layers=2, dropout=0.2):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=dropout)
        self.linear = nn.Linear(hidden_size, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.linear(out[:, -1, :])


class LSTMModel(BaseModel):
    name = "LSTM"

    def __init__(self):
        super().__init__()
        self.scaler_ = MinMaxScaler()
        self.lookback_ = config.LSTM_LOOKBACK
        self.epochs_ = config.LSTM_EPOCHS
        self.hidden_size_ = config.LSTM_UNITS
        self.dropout_ = config.LSTM_DROPOUT
        self._fitted_on_len = 0

    def _create_sequences(self, data):
        X, y = [], []
        for i in range(len(data) - self.lookback_):
            X.append(data[i:i + self.lookback_])
            y.append(data[i + self.lookback_])
        return np.array(X), np.array(y)

    def fit(self, series: pd.Series, **kwargs):
        series = series.dropna().values.reshape(-1, 1)
        scaled = self.scaler_.fit_transform(series).flatten()
        self._fitted_on_len = len(scaled)

        X, y = self._create_sequences(scaled)
        if len(X) < 2:
            raise ValueError(f"Not enough data for LSTM (need > {self.lookback_}, got {len(scaled)})")

        X_t = torch.tensor(X, dtype=torch.float32).unsqueeze(-1)
        y_t = torch.tensor(y, dtype=torch.float32).unsqueeze(-1)

        model = _LSTMModule(input_size=1, hidden_size=self.hidden_size_, num_layers=2, dropout=self.dropout_)
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

        model.train()
        for epoch in range(self.epochs_):
            optimizer.zero_grad()
            out = model(X_t)
            loss = criterion(out, y_t)
            loss.backward()
            optimizer.step()

        self.model_ = model
        self._last_window_scaled_ = scaled
        self.fitted_ = True
        return self

    def predict(self, steps: int) -> pd.DataFrame:
        if not self.fitted_:
            raise RuntimeError("Model not fitted")
        self.model_.eval()

        last_window = self._last_window_scaled_[-self.lookback_:]

        preds_scaled = []
        window = last_window.copy()
        with torch.no_grad():
            for _ in range(steps):
                x = torch.tensor(window, dtype=torch.float32).view(1, self.lookback_, 1)
                p = self.model_(x).item()
                preds_scaled.append(p)
                window = np.roll(window, -1)
                window[-1] = p

        preds = self.scaler_.inverse_transform(np.array(preds_scaled).reshape(-1, 1)).flatten()

        residual_std = np.std(preds) * 0.1
        return pd.DataFrame({
            "forecast": preds,
            "lower_bound": preds - 1.96 * residual_std,
            "upper_bound": preds + 1.96 * residual_std,
        })

    def predict_in_sample(self, series: pd.Series) -> np.ndarray:
        if not self.fitted_:
            raise RuntimeError("Model not fitted")
        self.model_.eval()

        raw = series.dropna().values.reshape(-1, 1)
        scaled = self.scaler_.transform(raw).flatten()

        X, _ = self._create_sequences(scaled)
        if len(X) == 0:
            return np.zeros(len(raw))

        X_t = torch.tensor(X, dtype=torch.float32).unsqueeze(-1)
        with torch.no_grad():
            preds_scaled = self.model_(X_t).numpy().flatten()

        padded = np.full(len(raw), np.nan)
        padded[self.lookback_:] = preds_scaled
        if np.all(np.isnan(padded)):
            return np.zeros(len(raw))
        isnan = np.isnan(padded)
        padded[isnan] = np.nanmean(padded)
        return self.scaler_.inverse_transform(padded.reshape(-1, 1)).flatten()
