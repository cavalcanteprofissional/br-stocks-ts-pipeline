import logging

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import TimeSeriesSplit

from src.config import config

logger = logging.getLogger(__name__)


def train_test_split_ts(series: pd.Series, test_size: float | None = None):
    test_size = test_size or config.TEST_SIZE
    n = len(series)
    split_idx = int(n * (1 - test_size))
    train = series.iloc[:split_idx]
    test = series.iloc[split_idx:]
    return train, test


def mean_absolute_scaled_error(train: pd.Series, test: pd.Series, forecast: pd.Series) -> float:
    n = len(train)
    if n < 2:
        return np.nan
    naive_errors = np.abs(train.diff().dropna()).mean()
    if naive_errors == 0 or np.isnan(naive_errors):
        return np.nan
    return np.mean(np.abs(test.values - forecast.values)) / naive_errors


def compute_metrics(test: pd.Series, forecast: pd.Series, train: pd.Series | None = None) -> dict:
    test_arr = test.values
    forecast_arr = forecast.values

    mae = mean_absolute_error(test_arr, forecast_arr)
    rmse = np.sqrt(mean_squared_error(test_arr, forecast_arr))
    mape = np.mean(np.abs((test_arr - forecast_arr) / np.where(test_arr != 0, test_arr, 1e-10))) * 100
    mase = mean_absolute_scaled_error(train, test, forecast) if train is not None else np.nan

    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "mape": float(mape),
        "mase": float(mase),
    }


def cv_forecast_series(series: pd.Series, model_fn, n_splits: int | None = None, seasonal_period: int | None = None):
    n_splits = n_splits or config.CV_FOLDS
    series = series.dropna()

    if len(series) < n_splits + 1:
        logger.warning(f"Series too short for {n_splits}-fold CV")
        return {"mae": {"mean": np.nan, "std": np.nan}, "rmse": {"mean": np.nan, "std": np.nan}, "mape": {"mean": np.nan, "std": np.nan}}

    tscv = TimeSeriesSplit(n_splits=n_splits)
    scores = {"mae": [], "rmse": [], "mape": []}

    for train_idx, test_idx in tscv.split(series):
        train = series.iloc[train_idx]
        test = series.iloc[test_idx]
        try:
            model = model_fn(train)
            forecast = model.predict(n_periods=len(test))
            scores["mae"].append(mean_absolute_error(test, forecast))
            scores["rmse"].append(np.sqrt(mean_squared_error(test, forecast)))
            mape_val = np.mean(np.abs((test.values - forecast.values) / np.where(test.values != 0, test.values, 1e-10))) * 100
            scores["mape"].append(mape_val)
        except Exception as e:
            logger.warning(f"CV fold failed: {e}")
            continue

    return {
        k: {"mean": float(np.mean(v)), "std": float(np.std(v))}
        for k, v in scores.items()
        if len(v) > 0
    }


def validate_all(entities: dict[str, pd.DataFrame], model_fn) -> dict:
    returns_col = "Returns"
    results = {"per_entity": {}, "macro_avg": {}}

    for entity_id, df in entities.items():
        logger.info(f"Validating {entity_id}")

        if returns_col in df.columns:
            series = df[returns_col]
        else:
            series = df[config.VALUE_COLUMN]

        series = series.dropna()
        train, test = train_test_split_ts(series)

        try:
            model = model_fn(train)
            forecast = model.predict(n_periods=len(test))
            metrics = compute_metrics(test, forecast, train)
            cv_scores = cv_forecast_series(series, model_fn)
        except Exception as e:
            logger.error(f"Validation failed for {entity_id}: {e}")
            metrics = {"mae": np.nan, "rmse": np.nan, "mape": np.nan, "mase": np.nan}
            cv_scores = {"mae": {"mean": np.nan, "std": np.nan}, "rmse": {"mean": np.nan, "std": np.nan}, "mape": {"mean": np.nan, "std": np.nan}}

        results["per_entity"][entity_id] = {
            "metrics": metrics,
            "cv_scores": cv_scores,
            "train_size": len(train),
            "test_size": len(test),
        }

    valid_metrics = [v["metrics"] for v in results["per_entity"].values()]
    if valid_metrics:
        results["macro_avg"] = {
            k: float(np.nanmean([m[k] for m in valid_metrics]))
            for k in ["mae", "rmse", "mape", "mase"]
        }

    return results
