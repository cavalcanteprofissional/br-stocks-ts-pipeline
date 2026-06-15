import time
from abc import ABC, abstractmethod

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

from src.config import config


class BaseModel(ABC):
    name: str = "base"

    def __init__(self):
        self.model_ = None
        self.fitted_ = False
        self.fit_time_s_ = 0.0

    @abstractmethod
    def fit(self, series: pd.Series, **kwargs):
        ...

    @abstractmethod
    def predict(self, steps: int) -> pd.DataFrame:
        ...

    @abstractmethod
    def predict_in_sample(self, series: pd.Series) -> np.ndarray:
        ...

    def cross_validate(self, series: pd.Series, steps: int | None = None) -> float:
        steps = steps or config.FORECAST_HORIZON
        tscv = TimeSeriesSplit(n_splits=5)
        errors = []
        series = series.dropna()
        for train_idx, test_idx in tscv.split(series):
            train = series.iloc[train_idx]
            test = series.iloc[test_idx][:steps]
            if len(test) < 2:
                continue
            try:
                m = type(self)()
                m.fit(train)
                preds = m.predict(len(test))
                errors.append(float(np.sqrt(np.mean((preds["forecast"].values - test.values) ** 2))))
            except Exception:
                continue
        return float(np.mean(errors)) if errors else None

    def compute_metrics(self, series: pd.Series) -> dict:
        series = series.dropna()
        preds = self.predict_in_sample(series)
        y_true = series.values[-len(preds):]
        residuals = y_true - preds
        rmse = float(np.sqrt(np.mean(residuals ** 2)))
        mae = float(np.mean(np.abs(residuals)))
        mape = float(np.mean(np.abs(residuals / (np.abs(y_true) + 1e-10))) * 100)
        smape = float(np.mean(2.0 * np.abs(residuals) / (np.abs(y_true) + np.abs(preds) + 1e-10)) * 100)
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        r2 = float(1 - ss_res / (ss_tot + 1e-10))
        residual_std = float(np.std(residuals))
        return {
            "rmse": rmse,
            "mae": mae,
            "mape": mape,
            "smape": smape,
            "r2": r2,
            "residual_std": residual_std,
        }

    def timed_fit(self, series: pd.Series, **kwargs):
        t0 = time.perf_counter()
        self.fit(series, **kwargs)
        self.fit_time_s_ = time.perf_counter() - t0
        self.fitted_ = True
        return self
