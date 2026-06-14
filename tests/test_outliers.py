import numpy as np
import pandas as pd
import pytest

from src.outliers import detect_outliers_batch, compute_residual_stats, detect_anomaly_realtime


@pytest.fixture
def seasonal_series():
    np.random.seed(42)
    t = np.arange(200)
    trend = 0.01 * t
    seasonal = 5 * np.sin(2 * np.pi * t / 12)
    noise = np.random.randn(200) * 0.5
    values = 100 + trend + seasonal + noise
    values[50] += 50
    values[150] -= 40
    dates = pd.date_range("2020-01-01", periods=200, freq="ME")
    return pd.Series(values, index=dates, name="Close")


def test_detect_outliers_batch(seasonal_series):
    outliers = detect_outliers_batch(seasonal_series, period=12)
    assert isinstance(outliers, pd.DataFrame)
    if not outliers.empty:
        assert "date" in outliers.columns
        assert "severity" in outliers.columns


def test_compute_residual_stats(seasonal_series):
    stats = compute_residual_stats(seasonal_series, period=12)
    for key in ["mean", "std", "q1", "q3", "iqr", "threshold"]:
        assert key in stats
    assert stats["iqr"] > 0


def test_detect_anomaly_realtime():
    stats = {"mean": 0.0, "std": 1.0, "iqr": 1.5, "threshold": 2.25}
    normal = detect_anomaly_realtime(1.0, stats)
    assert not normal["is_anomaly"]
    assert normal["severity"] == "none"

    anomalous = detect_anomaly_realtime(5.0, stats)
    assert anomalous["is_anomaly"]
    assert anomalous["severity"] in ("medium", "high")
