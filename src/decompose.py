import logging

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statsmodels.tsa.seasonal import seasonal_decompose

from src.config import config

logger = logging.getLogger(__name__)


def auto_detect_model(series: pd.Series, period: int) -> str:
    series = series.dropna()
    if len(series) < period * 2:
        return "additive"

    try:
        add = seasonal_decompose(series, model="additive", period=period, extrapolate_trend="freq")
        mul = seasonal_decompose(series, model="multiplicative", period=period, extrapolate_trend="freq")
    except Exception:
        return "additive"

    add_resid_var = add.resid.dropna().var()
    mul_resid_var = mul.resid.dropna().var()

    if mul_resid_var < add_resid_var * 0.8:
        return "multiplicative"
    return "additive"


def decompose_entity(df: pd.DataFrame, period: int | None = None) -> dict:
    value_col = config.VALUE_COLUMN
    series = df[value_col]
    period = period or config.seasonal_period

    model = auto_detect_model(series, period)
    logger.info(f"Detected model: {model}, period: {period}")

    result = seasonal_decompose(
        series.dropna(),
        model=model,
        period=period,
        extrapolate_trend="freq",
    )

    return {
        "observed": result.observed,
        "trend": result.trend,
        "seasonal": result.seasonal,
        "resid": result.resid,
        "model": model,
        "period": period,
    }


def decompose_all(entities: dict[str, pd.DataFrame]) -> dict[str, dict]:
    results = {}
    for entity_id, df in entities.items():
        logger.info(f"Decomposing {entity_id}")
        results[entity_id] = decompose_entity(df)
    return results


def plot_decomposition(result: dict, title: str = "") -> go.Figure:
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        subplot_titles=("Observed", "Trend", "Seasonal", "Residual"),
        vertical_spacing=0.05,
    )

    panels = [
        ("observed", None),
        ("trend", None),
        ("seasonal", None),
        ("resid", None),
    ]

    for i, (key, _) in enumerate(panels, 1):
        series = result[key]
        if series is None or series.dropna().empty:
            continue
        fig.add_trace(
            go.Scatter(x=series.index, y=series.values, mode="lines", showlegend=False),
            row=i, col=1,
        )

    fig.update_layout(
        title=title or f"Decomposition ({result['model']}, period={result['period']})",
        height=700,
    )
    return fig
