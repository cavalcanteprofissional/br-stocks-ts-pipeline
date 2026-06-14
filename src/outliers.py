import logging

import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose

from src.config import config

logger = logging.getLogger(__name__)


def detect_outliers_batch(
    series: pd.Series,
    period: int | None = None,
    multiplier: float | None = None,
) -> pd.DataFrame:
    period = period or config.seasonal_period
    multiplier = multiplier or config.ANOMALY_THRESHOLD

    series = series.dropna()
    if len(series) < period * 2:
        logger.warning(f"Series too short ({len(series)} < {period * 2}) for decomposition")
        return pd.DataFrame()

    result = seasonal_decompose(series, model="additive", period=period, extrapolate_trend="freq")
    resid = result.resid.dropna()

    Q1 = resid.quantile(0.25)
    Q3 = resid.quantile(0.75)
    iqr = Q3 - Q1
    lower = Q1 - multiplier * iqr
    upper = Q3 + multiplier * iqr

    mask = (resid < lower) | (resid > upper)
    flagged = resid[mask]

    if len(flagged) == 0:
        return pd.DataFrame()

    result_df = pd.DataFrame({
        "date": flagged.index,
        "value": series.loc[flagged.index],
        "residual": flagged.values,
        "lower_bound": lower,
        "upper_bound": upper,
        "severity": pd.cut(
            flagged.values,
            bins=[-np.inf, lower * 3, lower, upper, upper * 3, np.inf],
            labels=["extreme_low", "low", "normal", "high", "extreme_high"],
        ),
    })
    return result_df


def compute_residual_stats(
    series: pd.Series,
    period: int | None = None,
) -> dict:
    period = period or config.seasonal_period
    series = series.dropna()

    result = seasonal_decompose(series, model="additive", period=period, extrapolate_trend="freq")
    resid = result.resid.dropna()

    Q1 = resid.quantile(0.25)
    Q3 = resid.quantile(0.75)
    iqr = Q3 - Q1

    return {
        "mean": float(resid.mean()),
        "std": float(resid.std()),
        "q1": float(Q1),
        "q3": float(Q3),
        "iqr": float(iqr),
        "threshold": float(iqr * config.ANOMALY_THRESHOLD),
    }


def detect_anomaly_realtime(
    new_value: float,
    historical_stats: dict,
) -> dict:
    deviation = abs(new_value - historical_stats["mean"])
    threshold = historical_stats["threshold"]
    is_anomaly = deviation > threshold

    severity = "none"
    if is_anomaly:
        severity = "high" if deviation > threshold * 2 else "medium"

    return {
        "is_anomaly": is_anomaly,
        "deviation": deviation,
        "threshold": threshold,
        "severity": severity,
    }
