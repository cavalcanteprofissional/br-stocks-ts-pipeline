import logging

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, kpss
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.stats.stattools import jarque_bera
from pmdarima import auto_arima

from src.config import config

logger = logging.getLogger(__name__)


def check_stationarity(series: pd.Series) -> dict:
    series = series.dropna()
    if len(series) < 10:
        return {"adf_stationary": False, "kpss_stationary": False, "d_suggested": 1}

    adf = adfuller(series)
    kpss_result = kpss(series, regression="ct", nlags="auto")

    results = {
        "adf_stat": float(adf[0]),
        "adf_pval": float(adf[1]),
        "adf_stationary": bool(adf[1] < 0.05),
        "kpss_stat": float(kpss_result[0]),
        "kpss_pval": float(kpss_result[1]),
        "kpss_stationary": bool(kpss_result[1] >= 0.05),
    }

    if results["adf_stationary"] and results["kpss_stationary"]:
        results["d_suggested"] = 0
    elif not results["adf_stationary"] and results["kpss_stationary"]:
        results["d_suggested"] = 1
    elif results["adf_stationary"] and not results["kpss_stationary"]:
        results["d_suggested"] = 0
    else:
        results["d_suggested"] = 1

    return results


def fit_arima(series: pd.Series, seasonal_period: int | None = None, d: int | None = None):
    series = series.dropna()
    if len(series) < 24:
        logger.warning(f"Series too short ({len(series)} < 24), may not converge")

    period = seasonal_period or config.seasonal_period
    has_seasonality = len(series) >= period * 2

    model = auto_arima(
        series,
        start_p=0, max_p=5,
        start_q=0, max_q=5,
        d=d,
        start_P=0, max_P=2 if has_seasonality else 0,
        start_Q=0, max_Q=2 if has_seasonality else 0,
        D=None if has_seasonality else 0,
        m=period if has_seasonality else 1,
        seasonal=has_seasonality,
        trace=False,
        error_action="ignore",
        suppress_warnings=True,
        stepwise=True,
        information_criterion="aic",
        max_iter=50,
        random_state=42,
    )

    return model


def fit_all(entities: dict[str, pd.DataFrame]) -> dict[str, dict]:
    results = {}
    returns_col = "Returns"

    for entity_id, df in entities.items():
        logger.info(f"Modeling {entity_id}")

        if returns_col in df.columns:
            series = df[returns_col]
        else:
            series = df[config.VALUE_COLUMN]

        stationarity = check_stationarity(series)
        d = stationarity["d_suggested"]
        logger.info(f"{entity_id}: d={d}, ADF p={stationarity['adf_pval']:.4f}, KPSS p={stationarity['kpss_pval']:.4f}")

        model = fit_arima(series, d=d)
        diagnostics = model_diagnostics(model, series)

        results[entity_id] = {
            "model": model,
            "stationarity": stationarity,
            "diagnostics": diagnostics,
            "aic": model.aic(),
            "bic": model.bic(),
            "order": (model.order, model.seasonal_order),
        }

    return results


def model_diagnostics(model, series: pd.Series) -> dict:
    try:
        resid = model.resid()
    except Exception:
        try:
            resid = pd.Series(model.resid)
        except Exception:
            resid = pd.Series(series.dropna() - model.predict_in_sample())

    resid = resid.dropna()

    lb = acorr_ljungbox(resid, lags=[min(10, len(resid) // 2 - 1)], return_df=True)
    lb_pval = lb["lb_pvalue"].iloc[0] if len(lb) > 0 else 1.0

    try:
        jb_stat, jb_pval = jarque_bera(resid)
    except Exception:
        jb_stat, jb_pval = 0.0, 1.0

    return {
        "residuals": resid,
        "ljung_box_pvalue": float(lb_pval),
        "jarque_bera_stat": float(jb_stat),
        "jarque_bera_pval": float(jb_pval),
        "has_residual_autocorrelation": bool(lb_pval < 0.05),
    }


def forecast(model, steps: int | None = None) -> pd.DataFrame:
    steps = steps or config.FORECAST_HORIZON
    preds, conf_int = model.predict(n_periods=steps, return_conf_int=True)

    forecast_df = pd.DataFrame({
        "forecast": preds,
        "lower_bound": conf_int[:, 0],
        "upper_bound": conf_int[:, 1],
    })
    return forecast_df
