import logging

import numpy as np
import pandas as pd
from prophet import Prophet

from src.models.base import BaseModel

logger = logging.getLogger(__name__)


class ProphetModel(BaseModel):
    name = "Prophet"

    def fit(self, series: pd.Series, **kwargs):
        series = series.dropna()
        df = pd.DataFrame({"ds": series.index, "y": series.values})
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
            interval_width=0.95,
        )
        model.fit(df)
        self.model_ = model
        self.fitted_ = True
        return self

    def predict(self, steps: int) -> pd.DataFrame:
        if not self.fitted_:
            raise RuntimeError("Model not fitted")
        future = self.model_.make_future_dataframe(periods=steps, include_history=False)
        fc = self.model_.predict(future)
        return pd.DataFrame({
            "forecast": fc["yhat"].values,
            "lower_bound": fc["yhat_lower"].values,
            "upper_bound": fc["yhat_upper"].values,
        })

    def predict_in_sample(self, series: pd.Series) -> np.ndarray:
        if not self.fitted_:
            raise RuntimeError("Model not fitted")
        df = pd.DataFrame({"ds": series.index, "y": series.values})
        fc = self.model_.predict(df)
        return fc["yhat"].values
