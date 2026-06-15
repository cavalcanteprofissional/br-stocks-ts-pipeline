import logging

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, kpss
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.stats.stattools import jarque_bera

from src.config import config
from src.models import MODEL_REGISTRY
from src.models.arima_model import ARIMAModel

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

    model = ARIMAModel()
    model.fit(series, seasonal_period=seasonal_period, d=d)
    return model.model_


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

        model_obj = ARIMAModel()
        model_obj.fit(series, d=d)
        diag = model_diagnostics(model_obj.model_, series)

        results[entity_id] = {
            "model": model_obj.model_,
            "stationarity": stationarity,
            "diagnostics": diag,
            "aic": model_obj.aic_,
            "bic": model_obj.bic_,
            "order": (model_obj.order_, model_obj.seasonal_order_),
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
