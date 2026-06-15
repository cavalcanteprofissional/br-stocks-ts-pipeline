import base64
import json
import math
from pathlib import Path

import numpy as np

DATA_PATH = Path("data/dashboard_data.json")
OUT_PATH = Path("landing/public/landing_data.json")


def _sanitize(obj):
    """Recursively replace float('nan') with None for valid JSON output."""
    if isinstance(obj, float) and math.isnan(obj):
        return None
    if isinstance(obj, list):
        return [_sanitize(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    return obj


def _decode_typed_array(val):
    """Decode Plotly typed array {dtype: 'f8', bdata: 'base64...'} to list, NaN → None."""
    if isinstance(val, dict) and "dtype" in val and "bdata" in val:
        arr = np.frombuffer(base64.b64decode(val["bdata"]), dtype=val["dtype"])
        return [None if math.isnan(x) else x for x in arr.tolist()]
    return val


def _extract_trace_value(tr, key):
    """Extract a trace value, decoding typed arrays and reshaping heatmap z."""
    val = tr.get(key)
    val = _decode_typed_array(val)
    if key == "z" and isinstance(val, list) and len(val) > 0:
        x_len = len(tr.get("x", []))
        y_len = len(tr.get("y", []))
        if x_len and not isinstance(val[0], list) and len(val) == x_len * y_len:
            return [val[i * x_len:(i + 1) * x_len] for i in range(y_len)]
    return val


def extract_chart_data(charts, key):
    raw = charts.get(key)
    if not raw:
        return None
    traces = raw.get("data", [])
    out = {"traces": []}
    for tr in traces:
        t = {}
        for field in ("x", "y", "z", "name", "type"):
            if field in tr:
                t[field] = _extract_trace_value(tr, field)
        if "marker" in tr and "colors" in tr["marker"]:
            t["colors"] = tr["marker"]["colors"]
        out["traces"].append(t)
    layout = raw.get("layout", {})
    if "title" in layout:
        title = layout["title"]
        out["title"] = title.get("text", "") if isinstance(title, dict) else str(title)
    return out


def compute_drawdown(close_prices):
    if not close_prices:
        return []
    peak = close_prices[0]
    dd = []
    for p in close_prices:
        if p > peak:
            peak = p
        dd.append((p - peak) / peak * 100 if peak else 0)
    return dd


def main():
    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)

    meta = data["metadata"]
    kpis = data["kpis"]
    charts_raw = data.get("charts", {})

    best_entity = kpis["overall"]["best_entity"]
    worst_entity = kpis["overall"]["worst_entity"]

    series = data.get("series", {})

    best_series = series.get(best_entity, {})
    worst_series = series.get(worst_entity, {})
    best_dates = best_series.get("dates", [])
    best_close = best_series.get("Close", [])
    worst_dates = worst_series.get("dates", [])
    worst_close = worst_series.get("Close", [])

    landing = {
        "metadata": {
            "generated_at": meta["generated_at"],
            "tickers": meta["tickers"],
            "value_column": meta["value_column"],
            "resample_freq": meta["resample_freq"],
            "forecast_horizon": meta["forecast_horizon"],
        },
        "kpis": {
            "overall": {
                "best_entity": best_entity,
                "best_return": kpis["overall"]["best_return"],
                "worst_entity": worst_entity,
                "worst_return": kpis["overall"]["worst_return"],
                "all_returns": kpis["overall"]["all_returns"],
            },
            "entities": kpis.get("entities", {}),
        },
        "entity_series": {
            best_entity: {"dates": best_dates, "Close": best_close,
                          "Drawdown": compute_drawdown(best_close)},
            worst_entity: {"dates": worst_dates, "Close": worst_close,
                           "Drawdown": compute_drawdown(worst_close)},
        },
        "charts": {
            "correlation": extract_chart_data(charts_raw, "correlation"),
            "monthly_returns": extract_chart_data(charts_raw, "monthly_returns"),
        },
        "forecast": data.get("forecast", {}),
    }

    landing = _sanitize(landing)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(landing, f, ensure_ascii=False)

    size_kb = OUT_PATH.stat().st_size / 1024
    print(f"OK - Landing data written ({size_kb:.1f} KB): {OUT_PATH}")


if __name__ == "__main__":
    main()
