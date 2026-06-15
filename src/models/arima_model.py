import logging

import numpy as np
import pandas as pd
from pmdarima import auto_arima
from pmdarima.arima import ARIMA

from src.config import config
from src.models.base import BaseModel

logger = logging.getLogger(__name__)


class ARIMAModel(BaseModel):
    name = "ARIMA"

    def __init__(self):
        super().__init__()
        self.order_ = None
        self.seasonal_order_ = None
        self.aic_ = None
        self.bic_ = None
        self.diagnostics_ = {}

    def fit(self, series: pd.Series, seasonal_period: int | None = None, d: int | None = None):
        series = series.dropna()
        period = seasonal_period or config.seasonal_period
        has_seasonality = len(series) >= period * 2

        auto = auto_arima(
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
        self.model_ = auto
        self.order_ = auto.order
        self.seasonal_order_ = auto.seasonal_order
        self.aic_ = auto.aic()
        self.bic_ = auto.bic()
        self.fitted_ = True
        return self

    def predict(self, steps: int) -> pd.DataFrame:
        if not self.fitted_:
            raise RuntimeError("Model not fitted")
        preds, conf_int = self.model_.predict(n_periods=steps, return_conf_int=True)
        return pd.DataFrame({
            "forecast": preds,
            "lower_bound": conf_int[:, 0],
            "upper_bound": conf_int[:, 1],
        })

    def predict_in_sample(self, series: pd.Series) -> np.ndarray:
        if not self.fitted_:
            raise RuntimeError("Model not fitted")
        return self.model_.predict_in_sample()

    def refit(self, series: pd.Series):
        if self.order_ is None:
            return self.fit(series)
        arima = ARIMA(order=self.order_, seasonal_order=self.seasonal_order_)
        arima.fit(series)
        self.model_ = arima
        self.fitted_ = True
        return self

    def to_dict(self) -> dict:
        return {
            "order": list(self.order_) if self.order_ else None,
            "seasonal_order": list(self.seasonal_order_) if self.seasonal_order_ else None,
            "aic": self.aic_,
            "bic": self.bic_,
        }
