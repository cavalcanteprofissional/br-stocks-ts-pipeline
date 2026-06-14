# Brazilian Stocks - Time Series Analysis Pipeline

Automated time series analysis pipeline for multi-stock forecasting with ARIMA/SARIMA, anomaly detection, and an interactive Streamlit dashboard.

**Domain:** Financial (Brazilian stocks via Yahoo Finance)  
**Frequency:** Daily → resampled to weekly for modeling  
**Entities:** 10 representative tickers across multiple sectors

## Features

- **Data ingestion** — Yahoo Finance API (auto-cached) + CSV/Parquet + PostgreSQL
- **Preprocessing** — resampling, gap filling, log returns, lag/rolling features
- **Exploratory analysis** — 8 interactive Plotly plots (series, returns, seasonality, correlation, volatility, ACF/PACF, etc.)
- **Seasonal decomposition** — auto-detects additive vs multiplicative model
- **Outlier detection** — IQR on decomposition residuals (batch) + real-time anomaly check
- **Stationarity tests** — ADF + KPSS per entity with auto-differencing
- **ARIMA/SARIMA modeling** — auto order detection via `pmdarima.auto_arima`
- **Model diagnostics** — Ljung-Box, Jarque-Bera, residual ACF/PACF
- **Validation** — train/test split + time series cross-validation (forward chaining)
- **Metrics** — MAE, RMSE, MAPE, MASE per entity + macro average
- **Forecast** — multi-step predictions with confidence intervals
- **Interactive dashboard** — Streamlit with 6 tabs (Overview, EDA, Decomposition, Model, Forecast, Anomalies)
- **Real-time anomaly monitor** — standalone class for streaming/API integration

## Architecture

```
st/
├── data/                     # CSV cache from Yahoo Finance
├── results/                  # Pipeline output (figures, CSVs, metrics)
├── src/
│   ├── config.py             # Central configuration (dataclass)
│   ├── ingest.py             # Data ingestion (yfinance / file / postgres)
│   ├── preprocess.py         # Resampling, returns, features
│   ├── eda.py                # Exploratory plots (Plotly)
│   ├── decompose.py          # Seasonal decomposition (auto additive/multiplicative)
│   ├── outliers.py           # Batch + real-time anomaly detection
│   ├── modeling.py           # Stationarity, auto_arima, diagnostics
│   ├── validation.py         # Train/test split, CV, metrics
│   ├── pipeline.py           # CLI orchestrator (argparse)
│   ├── dashboard.py          # Streamlit app
│   └── anomaly_monitor.py    # Reusable real-time anomaly checker
├── tests/
│   ├── test_preprocess.py
│   ├── test_modeling.py
│   └── test_outliers.py
├── pyproject.toml            # Poetry configuration
├── poetry.lock               # Locked dependencies
├── plano_implementacao.md
└── README.md
```

## Installation

### Prerequisites
- Python >=3.11
- [Poetry](https://python-poetry.org/) (dependency manager)

### Setup

```bash
# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

## Quick Start

### 1. Run the full pipeline

```bash
poetry run python src/pipeline.py
```

Downloads data for 10 Brazilian stocks, preprocesses, decomposes, fits ARIMA/SARIMA models, validates, and exports results to `./results/`.

### 2. Custom tickers and settings

```bash
poetry run python src/pipeline.py \
    --tickers "PETR4.SA,VALE3.SA,ITUB4.SA" \
    --forecast-horizon 12 \
    --period 52 \
    --output-dir ./results
```

### 3. Launch the dashboard

```bash
poetry run streamlit run src/dashboard.py
```

Or run pipeline + dashboard in sequence:

```bash
poetry run python src/pipeline.py --dashboard
```

### 4. Real-time anomaly check

```bash
poetry run python -c "
from src.anomaly_monitor import AnomalyMonitor
m = AnomalyMonitor()
print(m.check('PETR4.SA', '2025-06-01', 42.50))
"
```

## CLI Reference

| Argument | Default | Description |
|---|---|---|
| `--source` | `api` | Data source: `api`, `file`, or `postgres` |
| `--file-path` | — | Path to CSV/Parquet (file mode) |
| `--tickers` | 10 default | Comma-separated ticker symbols (api mode) |
| `--start-date` | `2015-01-01` | Start date (YYYY-MM-DD) |
| `--end-date` | `2025-12-31` | End date (YYYY-MM-DD) |
| `--forecast-horizon` | `12` | Number of forecast steps |
| `--period` | auto | Seasonal period (inferred from freq) |
| `--output-dir` | `./results` | Output directory |
| `--dashboard` | — | Launch Streamlit after pipeline |
| `--skip-eda` | — | Skip EDA plots |
| `--skip-decompose` | — | Skip decomposition |
| `--skip-model` | — | Skip modeling |

## Configuration

Edit `src/config.py` or set environment variables:

```python
DATA_SOURCE = "api"           # api | file | postgres
TICKERS = ["PETR4.SA", ...]   # Stock tickers
RESAMPLE_FREQ = "W"           # Target frequency (W, ME, D)
FORECAST_HORIZON = 12         # Steps to forecast
TEST_SIZE = 0.2               # Test fraction
CV_FOLDS = 5                  # Cross-validation folds
ANOMALY_THRESHOLD = 1.5       # IQR multiplier
```

For PostgreSQL mode, set `DB_URL` in a `.env` file:

```env
DB_URL=postgresql://user:pass@localhost:5432/mydb
```

## Default Tickers

| Ticker | Company | Sector |
|---|---|---|
| PETR4.SA | Petrobras | Oil & Gas |
| VALE3.SA | Vale | Mining |
| ITUB4.SA | Itaú Unibanco | Banking |
| BBDC4.SA | Bradesco | Banking |
| ABEV3.SA | Ambev | Beverages |
| WEGE3.SA | WEG | Industry |
| BBAS3.SA | Banco do Brasil | Banking |
| ELET3.SA | Eletrobras | Energy |
| B3SA3.SA | B3 | Financial (Exchange) |
| RENT3.SA | Localiza | Car Rental |

## Testing

```bash
poetry run pytest tests/ -v
```

## Pipeline Steps

1. **Ingest** — load data from yfinance (or file/postgres)
2. **Preprocess** — resample to weekly, fill gaps, compute log returns, engineer features
3. **EDA** — generate 8 Plotly figures (saved as JSON)
4. **Decompose** — auto-detect model, seasonal decomposition, batch outlier detection
5. **Model** — ADF/KPSS stationarity tests, auto_arima per entity, diagnostics
6. **Validate** — train/test split, forward-chaining CV, export metrics
7. **Forecast** — future predictions with confidence intervals (converted back to price)
8. **Export** — CSVs + Plotly JSON + metrics summary
