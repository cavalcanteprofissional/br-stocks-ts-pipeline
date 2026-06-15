import logging
from pathlib import Path

import pandas as pd

from src.config import config

logger = logging.getLogger(__name__)


def ingest() -> dict[str, pd.DataFrame]:
    if config.DATA_SOURCE == "api":
        return _ingest_from_api()
    elif config.DATA_SOURCE == "file":
        return _ingest_from_file()
    elif config.DATA_SOURCE == "postgres":
        return _ingest_from_postgres()
    else:
        raise ValueError(f"Unknown DATA_SOURCE: {config.DATA_SOURCE}")


def _ingest_from_api() -> dict[str, pd.DataFrame]:
    import yfinance as yf

    cache_dir = Path(config.CACHE_DIR)
    cache_dir.mkdir(parents=True, exist_ok=True)

    entities = {}

    for ticker in config.TICKERS:
        cache_path = cache_dir / f"{ticker}.csv"
        try:
            logger.info(f"Downloading {ticker} from Yahoo Finance")
            data = yf.download(
                ticker,
                start=config.START_DATE,
                end=config.END_DATE,
                auto_adjust=True,
                progress=False,
            )
        except Exception as e:
            logger.warning(f"API error for {ticker}: {e}")
            data = pd.DataFrame()

        if data.empty:
            logger.warning(f"No API data for {ticker}")
            if cache_path.exists():
                logger.info(f"Falling back to cached CSV for {ticker}")
                df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
            else:
                logger.warning(f"No cached data for {ticker}, skipping")
                continue
        else:
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.droplevel(1)

            df = data.reset_index()
            df.to_csv(cache_path, index=False)
            df = pd.read_csv(cache_path, index_col=0, parse_dates=True)

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)

        if not df.empty and config.VALUE_COLUMN in df.columns:
            df[config.VALUE_COLUMN] = pd.to_numeric(df[config.VALUE_COLUMN], errors="coerce")
            entities[ticker] = df[[config.VALUE_COLUMN]]
        elif not df.empty:
            entities[ticker] = df

    if not entities:
        raise RuntimeError("No data loaded for any ticker")

    return entities


def _ingest_from_file() -> dict[str, pd.DataFrame]:
    path = Path(config.FILE_PATH)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(path, parse_dates=True)
    elif suffix == ".parquet":
        df = pd.read_parquet(path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")

    required = [config.DATE_COLUMN, config.VALUE_COLUMN]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df[config.DATE_COLUMN] = pd.to_datetime(df[config.DATE_COLUMN])

    entities = {}
    for entity_id, group in df.groupby(config.TICKERS[0] if len(config.TICKERS) == 1 else "entity"):
        group = group.set_index(config.DATE_COLUMN).sort_index()
        entities[entity_id] = group[[config.VALUE_COLUMN]]

    return entities


def _ingest_from_postgres() -> dict[str, pd.DataFrame]:
    from sqlalchemy import create_engine, text

    engine = create_engine(config.DB_URL)
    entity_col = config.TICKERS[0] if len(config.TICKERS) == 1 else "entity"

    query = text(f"""
        SELECT {entity_col}, {config.DATE_COLUMN}, {config.VALUE_COLUMN}
        FROM {config.FILE_PATH}
        WHERE {config.DATE_COLUMN} BETWEEN :start AND :end
        ORDER BY {entity_col}, {config.DATE_COLUMN}
    """)

    df = pd.read_sql(
        query,
        engine,
        params={"start": config.START_DATE, "end": config.END_DATE},
        parse_dates=[config.DATE_COLUMN],
    )

    entities = {}
    for entity_id, group in df.groupby(entity_col):
        group = group.set_index(config.DATE_COLUMN).sort_index()
        entities[entity_id] = group[[config.VALUE_COLUMN]]

    return entities
