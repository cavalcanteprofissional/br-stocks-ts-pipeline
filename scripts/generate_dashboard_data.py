import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.io as pio
from pmdarima import auto_arima

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import config
from src.ingest import ingest
from src.preprocess import preprocess
from src.eda import (
    plot_series, plot_drawdown, plot_returns_with_context,
    plot_seasonal_boxplot, plot_distribution, plot_correlation,
    plot_volatility, plot_acf_pacf, plot_calendar_heatmap,
    plot_monthly_returns_heatmap, plot_top_entities_comparison,
    _best_worst_entities,
)
from src.decompose import decompose_all as decompose_all_entities
from src.modeling import check_stationarity, forecast as forecast_model
from src.outliers import detect_outliers_batch, compute_residual_stats

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_PATH = Path(config.CACHE_DIR) / "dashboard_data.json"
VALUE_COL = config.VALUE_COLUMN
FREQ = config.RESAMPLE_FREQ
FORECAST_HORIZON = config.FORECAST_HORIZON


class NumpyEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (np.integer, int)):
            return int(o)
        if isinstance(o, (np.floating, float)):
            if np.isnan(o) or np.isinf(o):
                return None
            return float(o)
        if isinstance(o, np.bool_):
            return bool(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, pd.Timestamp):
            return o.isoformat()
        if isinstance(o, pd.Series):
            return o.tolist()
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


def _series_to_dict(series: pd.Series) -> dict:
    dates = [d.isoformat() if isinstance(d, (pd.Timestamp, datetime)) else str(d)
             for d in series.index]
    values = [None if (isinstance(v, float) and (np.isnan(v) or np.isinf(v))) else v
              for v in series.values]
    return {"dates": dates, "values": values}


def _safe_float(v):
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return None
    return float(v)


def generate():
    logger.info("Loading data...")
    raw = ingest()
    entities = preprocess(raw)

    entity_ids = list(entities.keys())
    logger.info(f"Entities loaded: {entity_ids}")

    value_col = config.VALUE_COLUMN
    data = {}

    data["metadata"] = {
        "generated_at": datetime.now().isoformat(),
        "tickers": entity_ids,
        "value_column": VALUE_COL,
        "resample_freq": FREQ,
        "forecast_horizon": FORECAST_HORIZON,
        "seasonal_period": config.seasonal_period,
    }

    logger.info("Exporting series data...")
    series_data = {}
    for eid in entity_ids:
        df = entities[eid]
        s = df[value_col]
        ret = df["Returns"] if "Returns" in df.columns else pd.Series(dtype=float)
        series_data[eid] = {
            "dates": [d.isoformat() for d in s.index],
            "Close": [_safe_float(v) for v in s.values],
            "Returns": [_safe_float(v) for v in ret.values] if not ret.empty else [],
        }
    data["series"] = series_data

    logger.info("Computing KPIs...")
    worst_id, best_id, all_returns = _best_worst_entities(entities, value_col)
    data["kpis"] = {"overall": {}, "entities": {}}
    if best_id is not None:
        data["kpis"]["overall"] = {
            "best_entity": best_id,
            "best_return": _safe_float(all_returns.get(best_id)),
            "worst_entity": worst_id,
            "worst_return": _safe_float(all_returns.get(worst_id)),
            "all_returns": {k: _safe_float(v) for k, v in sorted(all_returns.items())},
        }

    entity_kpis = {}
    for eid in entity_ids:
        s = entities[eid][value_col].dropna()
        if s.empty:
            entity_kpis[eid] = {}
            continue
        total_return = _safe_float((s.iloc[-1] / s.iloc[0] - 1) * 100)
        peak_val = _safe_float(s.max())
        peak_date = s.idxmax().isoformat() if not s.empty else None
        current_val = _safe_float(s.iloc[-1])
        entity_kpis[eid] = {
            "total_return_pct": total_return,
            "peak_value": peak_val,
            "peak_date": peak_date,
            "current_close": current_val,
        }
    data["kpis"]["entities"] = entity_kpis

    logger.info("Generating EDA charts...")
    chart_fns = {
        "series": lambda: plot_series(entities),
        "drawdown": lambda: plot_drawdown(entities),
        "returns_with_context": lambda: plot_returns_with_context(entities),
        "top_vs_bottom": lambda: plot_top_entities_comparison(entities),
        "seasonal_boxplot": lambda: plot_seasonal_boxplot(entities),
        "calendar_heatmap": lambda: plot_calendar_heatmap(entities),
        "distribution": lambda: plot_distribution(entities),
        "correlation": lambda: plot_correlation(entities),
        "volatility": lambda: plot_volatility(entities),
        "acf_pacf": lambda: plot_acf_pacf(entities),
        "monthly_returns": lambda: plot_monthly_returns_heatmap(entities),
    }
    charts = {}
    for name, fn in chart_fns.items():
        try:
            fig = fn()
            charts[name] = json.loads(pio.to_json(fig))
            logger.info(f"  Chart '{name}' OK")
        except Exception as exc:
            logger.warning(f"  Chart '{name}' failed: {exc}")
            charts[name] = None
    data["charts"] = charts

    logger.info("Running decomposition...")
    dec_all = decompose_all_entities(entities)
    dec_export = {}
    for eid, dec in dec_all.items():
        dec_export[eid] = {
            "model": dec["model"],
            "period": dec["period"],
            "observed": _series_to_dict(dec["observed"]),
            "trend": _series_to_dict(dec["trend"]),
            "seasonal": _series_to_dict(dec["seasonal"]),
            "resid": _series_to_dict(dec["resid"]),
        }
    data["decomposition"] = dec_export

    logger.info("Fitting ARIMA models...")
    models_data = {}
    model_comp_rows = []
    for eid in entity_ids:
        df = entities[eid]
        ret = df["Returns"].dropna() if "Returns" in df.columns else df[value_col].dropna()
        if len(ret) < 10:
            logger.warning(f"  {eid}: insufficient data for modeling ({len(ret)} obs)")
            continue
        try:
            stat = check_stationarity(ret)
            d = stat.get("d_suggested", 0)
            period = config.seasonal_period
            has_seasonality = len(ret) >= period * 2
            model = auto_arima(
                ret,
                start_p=0, max_p=3,
                start_q=0, max_q=3,
                d=d,
                seasonal=has_seasonality,
                m=period if has_seasonality else 1,
                start_P=0, max_P=1,
                start_Q=0, max_Q=1,
                D=None if has_seasonality else 0,
                trace=False,
                error_action="ignore",
                suppress_warnings=True,
                stepwise=True,
                information_criterion="aic",
                max_iter=20,
                random_state=42,
            )
            order = model.order
            seas_order = model.seasonal_order
            aic = _safe_float(model.aic())
            bic = _safe_float(model.bic())
            models_data[eid] = {
                "order": list(order),
                "seasonal_order": list(seas_order),
                "aic": aic,
                "bic": bic,
                "stationarity": {
                    "adf_pval": _safe_float(stat.get("adf_pval")),
                    "kpss_pval": _safe_float(stat.get("kpss_pval")),
                    "d_suggested": stat.get("d_suggested"),
                },
            }
            if aic is not None:
                model_comp_rows.append({
                    "entity": eid, "order": str(order), "aic": aic,
                })
            logger.info(f"  {eid}: ARIMA{order} AIC={aic:.2f}")
        except Exception as exc:
            logger.warning(f"  {eid}: model failed: {exc}")

    data["models"] = models_data
    data["model_comparison"] = sorted(model_comp_rows, key=lambda r: r["aic"])

    logger.info("Generating forecasts...")
    forecasts = {}
    for eid in entity_ids:
        if eid not in models_data:
            continue
        df = entities[eid]
        ret = df["Returns"].dropna() if "Returns" in df.columns else df[value_col].dropna()
        try:
            stat = check_stationarity(ret)
            d = stat.get("d_suggested", 0)
            period = config.seasonal_period
            has_seasonality = len(ret) >= period * 2
            model = auto_arima(
                ret,
                start_p=0, max_p=3,
                start_q=0, max_q=3,
                d=d,
                seasonal=has_seasonality,
                m=period if has_seasonality else 1,
                start_P=0, max_P=1,
                start_Q=0, max_Q=1,
                D=None if has_seasonality else 0,
                trace=False,
                error_action="ignore",
                suppress_warnings=True,
                stepwise=True,
                information_criterion="aic",
                max_iter=20,
                random_state=42,
            )
            fc = forecast_model(model, FORECAST_HORIZON)
            last_date = df.index[-1]
            fc_dates = pd.date_range(start=last_date, periods=len(fc) + 1, freq=FREQ)[1:]

            last_price = float(df[value_col].iloc[-1]) if not df[value_col].dropna().empty else 0.0
            forecast_dict = {
                "dates": [d.isoformat() for d in fc_dates],
                "forecast": [_safe_float(v) for v in fc["forecast"].values],
                "lower_bound": [_safe_float(v) for v in fc["lower_bound"].values],
                "upper_bound": [_safe_float(v) for v in fc["upper_bound"].values],
            }
            if "Returns" in df.columns:
                fc_cumsum = np.cumsum(fc["forecast"].values)
                fc_lower_cumsum = np.cumsum(fc["lower_bound"].values)
                fc_upper_cumsum = np.cumsum(fc["upper_bound"].values)
                forecast_dict["price_forecast"] = [_safe_float(last_price * np.exp(v)) for v in fc_cumsum]
                forecast_dict["price_lower"] = [_safe_float(last_price * np.exp(v)) for v in fc_lower_cumsum]
                forecast_dict["price_upper"] = [_safe_float(last_price * np.exp(v)) for v in fc_upper_cumsum]

            forecasts[eid] = forecast_dict
            logger.info(f"  {eid}: forecast OK")
        except Exception as exc:
            logger.warning(f"  {eid}: forecast failed: {exc}")
    data["forecast"] = forecasts

    logger.info("Detecting outliers...")
    outliers_data = {}
    residual_stats = {}
    for eid in entity_ids:
        s = entities[eid][value_col]
        try:
            outliers_df = detect_outliers_batch(s)
            stats = compute_residual_stats(s)
            residual_stats[eid] = {k: _safe_float(v) for k, v in stats.items()}

            if not outliers_df.empty:
                outliers_data[eid] = {
                    "dates": [d.isoformat() for d in outliers_df["date"]],
                    "values": [_safe_float(v) for v in outliers_df["value"]],
                    "severities": [str(v) for v in outliers_df["severity"]],
                    "count": len(outliers_df),
                    "pct_total": _safe_float(len(outliers_df) / len(s.dropna()) * 100),
                }
            else:
                outliers_data[eid] = {"count": 0, "pct_total": 0.0}
            logger.info(f"  {eid}: {len(outliers_df)} outliers")
        except Exception as exc:
            logger.warning(f"  {eid}: outlier detection failed: {exc}")
            residual_stats[eid] = {}
            outliers_data[eid] = {"count": 0}
    data["outliers"] = outliers_data
    data["residual_stats"] = residual_stats

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, cls=NumpyEncoder, ensure_ascii=False, indent=2)

    logger.info(f"Dashboard data exported to {OUTPUT_PATH}")
    file_size_mb = OUTPUT_PATH.stat().st_size / (1024 * 1024)
    logger.info(f"File size: {file_size_mb:.2f} MB")


if __name__ == "__main__":
    generate()
