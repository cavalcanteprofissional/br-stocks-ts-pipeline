import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

from src.config import config


def walk_forward_cv(series: pd.Series, model_cls, steps: int | None = None) -> float:
    steps = steps or config.FORECAST_HORIZON
    tscv = TimeSeriesSplit(n_splits=5)
    errors = []
    series = series.dropna()
    for train_idx, test_idx in tscv.split(series):
        train = series.iloc[train_idx]
        test = series.iloc[test_idx][:steps]
        if len(test) < 2:
            continue
        try:
            m = model_cls()
            m.fit(train)
            preds = m.predict(len(test))
            errors.append(float(np.sqrt(np.mean((preds["forecast"].values - test.values) ** 2))))
        except Exception:
            continue
    return float(np.mean(errors)) if errors else None
