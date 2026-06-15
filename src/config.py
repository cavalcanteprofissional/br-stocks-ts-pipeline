from dataclasses import dataclass, field
from typing import Literal
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    DATA_SOURCE: Literal["api", "file", "postgres"] = "api"
    DB_URL: str = os.getenv("DB_URL", "")
    FILE_PATH: str = ""
    TICKERS: list[str] = field(default_factory=lambda: [
        "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA",
        "ABEV3.SA", "WEGE3.SA", "BBAS3.SA",
        "B3SA3.SA", "RENT3.SA",
    ])
    DATE_COLUMN: str = "Date"
    VALUE_COLUMN: str = "Close"
    FREQ: str = "D"
    RESAMPLE_FREQ: str = "W"
    FORECAST_HORIZON: int = 12
    TEST_SIZE: float = 0.2
    CV_FOLDS: int = 5
    ANOMALY_THRESHOLD: float = 1.5
    SEASONALITY_PERIOD: int | None = None
    START_DATE: str = "2015-01-01"
    END_DATE: str = "2025-12-31"
    OUTPUT_DIR: str = "./results"
    CACHE_DIR: str = "./data"

    @property
    def seasonal_period(self) -> int:
        if self.SEASONALITY_PERIOD is not None:
            return self.SEASONALITY_PERIOD
        period_map = {"W": 52, "ME": 12, "QE": 4, "YE": 1, "D": 5, "M": 12, "Q": 4, "Y": 1}
        return period_map.get(self.RESAMPLE_FREQ, 12)


config = Config()
