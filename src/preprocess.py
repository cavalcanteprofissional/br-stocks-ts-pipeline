import logging
import numpy as np
import pandas as pd

from src.config import config

logger = logging.getLogger(__name__)


def preprocess(entities: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    processed = {}
    for entity_id, df in entities.items():
        logger.info(f"Preprocessing {entity_id}")
        df = _ensure_date_index(df)
        df = _resample_and_fill(df)
        df = _compute_returns(df)
        df = _add_features(df)
        processed[entity_id] = df
    return processed


def _ensure_date_index(df: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(df.index, pd.DatetimeIndex):
        date_col = config.DATE_COLUMN
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col])
            df = df.set_index(date_col).sort_index()
        else:
            raise ValueError(f"Date column '{date_col}' not found")
    return df


def _resample_and_fill(df: pd.DataFrame) -> pd.DataFrame:
    freq = config.RESAMPLE_FREQ
    value_col = config.VALUE_COLUMN

    if df.index.freq is None:
        df = df.resample(freq).last()

    if df[value_col].isna().sum() > 0:
        total_gaps = df[value_col].isna().sum()
        total_len = len(df)
        gap_pct = total_gaps / total_len
        logger.info(f"Filling {total_gaps}/{total_len} gaps ({gap_pct:.1%})")

        if df[value_col].isna().all():
            logger.error(f"Column '{value_col}' is entirely NaN — cannot fill")
            return df

        df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
        df[value_col] = df[value_col].ffill(limit=2)
        df[value_col] = df[value_col].interpolate(method="linear", limit_direction="both")

        remaining = df[value_col].isna().sum()
        if remaining > 0:
            logger.warning(f"{remaining} gaps remain after filling — flagging for review")
            df["has_gap"] = df[value_col].isna()

    return df


def _compute_returns(df: pd.DataFrame) -> pd.DataFrame:
    value_col = config.VALUE_COLUMN
    df["Returns"] = np.log(df[value_col] / df[value_col].shift(1))
    df["Returns_simple"] = df[value_col].pct_change()
    return df


def _add_features(df: pd.DataFrame) -> pd.DataFrame:
    value_col = config.VALUE_COLUMN
    freq = config.RESAMPLE_FREQ

    df["lag_1"] = df[value_col].shift(1)
    df["lag_2"] = df[value_col].shift(2)
    df["lag_4"] = df[value_col].shift(4)

    window = 4 if freq == "W" else 3
    df[f"rolling_mean_{window}"] = df[value_col].rolling(window).mean()
    df[f"rolling_std_{window}"] = df[value_col].rolling(window).std()
    df[f"rolling_min_{window}"] = df[value_col].rolling(window).min()
    df[f"rolling_max_{window}"] = df[value_col].rolling(window).max()

    df["month"] = df.index.month
    df["quarter"] = df.index.quarter
    df["year"] = df.index.year
    df["week_of_year"] = df.index.isocalendar().week.astype(int)

    return df


def split_entities(entities: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    return entities
