from src.models.base import BaseModel
from src.models.arima_model import ARIMAModel
from src.models.prophet_model import ProphetModel

MODEL_REGISTRY: dict[str, type[BaseModel]] = {
    "ARIMA": ARIMAModel,
    "Prophet": ProphetModel,
}

try:
    from src.models.lstm_model import LSTMModel
    MODEL_REGISTRY["LSTM"] = LSTMModel
except ImportError:
    pass
