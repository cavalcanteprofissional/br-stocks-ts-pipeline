import numpy as np
import pandas as pd
import pytest

from src.modeling import check_stationarity, fit_arima, forecast


@pytest.fixture
def stationary_series():
    np.random.seed(42)
    values = np.random.randn(100).cumsum()
    dates = pd.date_range("2020-01-01", periods=100, freq="ME")
    return pd.Series(values, index=dates, name="Returns")


def test_check_stationarity(stationary_series):
    result = check_stationarity(stationary_series.diff().dropna())
    assert "adf_stationary" in result
    assert "kpss_stationary" in result
    assert "d_suggested" in result


def test_fit_arima(stationary_series):
    series = stationary_series.diff().dropna()
    model = fit_arima(series, seasonal_period=12, d=0)
    assert model is not None
    assert hasattr(model, "aic")
    assert model.aic() != float("inf")


def test_forecast(stationary_series):
    series = stationary_series.diff().dropna()
    model = fit_arima(series, seasonal_period=12, d=0)
    fc = forecast(model, steps=5)
    assert len(fc) == 5
    assert "forecast" in fc.columns
    assert "lower_bound" in fc.columns
    assert "upper_bound" in fc.columns
