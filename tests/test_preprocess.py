import numpy as np
import pandas as pd
import pytest

from src.config import config
from src.preprocess import _ensure_date_index, _resample_and_fill, _compute_returns, _add_features


@pytest.fixture
def sample_df():
    dates = pd.date_range("2020-01-01", periods=100, freq="D")
    values = np.random.randn(100).cumsum() + 100
    df = pd.DataFrame({"Close": values}, index=dates)
    df.index.name = "Date"
    return df


def test_ensure_date_index(sample_df):
    df_reset = sample_df.reset_index()
    result = _ensure_date_index(df_reset)
    assert isinstance(result.index, pd.DatetimeIndex)
    assert len(result) == len(sample_df)
    assert config.DATE_COLUMN not in result.columns


def test_resample_and_fill():
    dates = pd.date_range("2020-01-01", periods=20, freq="D")
    values = np.arange(20.0)
    values[5:7] = np.nan
    df = pd.DataFrame({"Close": values}, index=dates)
    result = _resample_and_fill(df)
    assert result["Close"].isna().sum() < values.size


def test_compute_returns(sample_df):
    result = _compute_returns(sample_df)
    assert "Returns" in result.columns
    assert "Returns_simple" in result.columns
    assert result["Returns"].iloc[0] is np.nan or pd.isna(result["Returns"].iloc[0])


def test_add_features(sample_df):
    result = _add_features(sample_df)
    for col in ["lag_1", "lag_2", "lag_4", "rolling_mean_4", "month", "quarter", "year"]:
        assert col in result.columns
