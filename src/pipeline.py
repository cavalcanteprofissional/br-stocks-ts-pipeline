import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

from src.config import config
from src.ingest import ingest
from src.preprocess import preprocess
from src.eda import (
    plot_series, plot_returns_with_context, plot_seasonal_boxplot,
    plot_distribution, plot_calendar_heatmap,
    plot_correlation, plot_acf_pacf, plot_volatility,
    plot_drawdown, plot_top_entities_comparison, plot_monthly_returns_heatmap,
)
from src.decompose import decompose_all, plot_decomposition
from src.outliers import detect_outliers_batch, compute_residual_stats
from src.modeling import fit_all, forecast as forecast_fn
from src.validation import validate_all

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("pipeline")


def parse_args():
    parser = argparse.ArgumentParser(description="Time Series Analysis Pipeline - Brazilian Stocks")
    parser.add_argument("--source", choices=["api", "file", "postgres"], default=None,
                        help="Data source (default: config.DATA_SOURCE)")
    parser.add_argument("--file-path", type=str, default=None,
                        help="Path to CSV/Parquet (file mode)")
    parser.add_argument("--tickers", type=str, default=None,
                        help="Comma-separated tickers (api mode)")
    parser.add_argument("--start-date", type=str, default=None,
                        help="Start date YYYY-MM-DD")
    parser.add_argument("--end-date", type=str, default=None,
                        help="End date YYYY-MM-DD")
    parser.add_argument("--forecast-horizon", type=int, default=None,
                        help="Number of steps to forecast")
    parser.add_argument("--period", type=int, default=None,
                        help="Seasonal period")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Output directory for results")
    parser.add_argument("--dashboard", action="store_true",
                        help="Launch Streamlit dashboard after pipeline")
    parser.add_argument("--skip-eda", action="store_true",
                        help="Skip EDA plots")
    parser.add_argument("--skip-decompose", action="store_true",
                        help="Skip decomposition")
    parser.add_argument("--skip-model", action="store_true",
                        help="Skip modeling")
    return parser.parse_args()


def run(args):
    logger.info("=" * 60)
    logger.info("Time Series Analysis Pipeline - Starting")
    logger.info("=" * 60)

    if args.source:
        config.DATA_SOURCE = args.source
    if args.file_path:
        config.FILE_PATH = args.file_path
    if args.tickers:
        config.TICKERS = [t.strip() for t in args.tickers.split(",")]
    if args.start_date:
        config.START_DATE = args.start_date
    if args.end_date:
        config.END_DATE = args.end_date
    if args.forecast_horizon:
        config.FORECAST_HORIZON = args.forecast_horizon
    if args.period:
        config.SEASONALITY_PERIOD = args.period
    if args.output_dir:
        config.OUTPUT_DIR = args.output_dir

    output_dir = Path(config.OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Source: {config.DATA_SOURCE}")
    logger.info(f"Tickers: {config.TICKERS}")
    logger.info(f"Forecast horizon: {config.FORECAST_HORIZON}")
    logger.info(f"Seasonal period: {config.seasonal_period}")

    logger.info("Step 1/6: Ingesting data...")
    raw_entities = ingest()
    logger.info(f"Loaded {len(raw_entities)} entities")

    logger.info("Step 2/6: Preprocessing...")
    entities = preprocess(raw_entities)
    logger.info(f"Preprocessed {len(entities)} entities")

    eda_figures = {}
    if not args.skip_eda:
        logger.info("Step 3/6: Generating EDA plots...")
        eda_figures["series"] = plot_series(entities)
        eda_figures["returns_with_context"] = plot_returns_with_context(entities)
        eda_figures["boxplot"] = plot_seasonal_boxplot(entities)
        eda_figures["distribution"] = plot_distribution(entities)
        eda_figures["correlation"] = plot_correlation(entities)
        eda_figures["volatility"] = plot_volatility(entities)
        eda_figures["drawdown"] = plot_drawdown(entities)
        eda_figures["top_comparison"] = plot_top_entities_comparison(entities)
        eda_figures["monthly_returns"] = plot_monthly_returns_heatmap(entities)

        show_first = list(entities.keys())[0]
        eda_figures["calendar_heatmap"] = plot_calendar_heatmap(entities)
        eda_figures["acf_pacf"] = plot_acf_pacf({show_first: entities[show_first]})

        for name, fig in eda_figures.items():
            fig.write_json(output_dir / f"eda_{name}.json")
            logger.info(f"Saved eda_{name}.json")

    decomposition_results = {}
    if not args.skip_decompose:
        logger.info("Step 4/6: Decomposing...")
        decomposition_results = decompose_all(entities)

        for entity_id, decomp in decomposition_results.items():
            fig = plot_decomposition(decomp, title=entity_id)
            fig.write_json(output_dir / f"decomp_{entity_id}.json")

        logger.info(f"Decomposed {len(decomposition_results)} entities")

    outlier_results = {}
    for entity_id, df in entities.items():
        series = df[config.VALUE_COLUMN]
        outliers = detect_outliers_batch(series)
        if not outliers.empty:
            outlier_results[entity_id] = outliers
            logger.info(f"{entity_id}: {len(outliers)} outliers detected")

    if outlier_results:
        all_outliers = pd.concat(
            {k: v for k, v in outlier_results.items()},
            names=["entity", "idx"],
        ).reset_index(level=0)
        all_outliers.to_csv(output_dir / "outliers.csv", index=False)
        logger.info(f"Saved outliers.csv ({len(all_outliers)} total)")

    model_results = {}
    validation_results = {}
    forecasts = {}
    if not args.skip_model:
        logger.info("Step 5/6: Modeling...")
        model_results = fit_all(entities)

        summary_rows = []
        for entity_id, result in model_results.items():
            order, seasonal_order = result["order"]
            diag = result["diagnostics"]
            summary_rows.append({
                "entity": entity_id,
                "order": f"{order}",
                "seasonal_order": f"{seasonal_order}",
                "aic": round(result["aic"], 2),
                "bic": round(result["bic"], 2),
                "lb_pvalue": round(diag["ljung_box_pvalue"], 4),
                "resid_autocorr": diag["has_residual_autocorrelation"],
            })
            logger.info(
                f"{entity_id}: ARIMA{order}{seasonal_order} "
                f"AIC={result['aic']:.2f} "
                f"LB p={diag['ljung_box_pvalue']:.4f}"
            )

        model_summary = pd.DataFrame(summary_rows)
        model_summary.to_csv(output_dir / "model_summary.csv", index=False)

        logger.info("Step 6/6: Validating...")

        def model_fn(series):
            from src.modeling import fit_arima
            return fit_arima(series)

        validation_results = validate_all(entities, model_fn)

        val_rows = []
        for entity_id, v in validation_results["per_entity"].items():
            val_rows.append({
                "entity": entity_id,
                **v["metrics"],
                "cv_mae_mean": v["cv_scores"]["mae"]["mean"],
                "cv_mae_std": v["cv_scores"]["mae"]["std"],
                "train_size": v["train_size"],
                "test_size": v["test_size"],
            })
        val_summary = pd.DataFrame(val_rows)
        val_summary.to_csv(output_dir / "validation_metrics.csv", index=False)

        macro = validation_results.get("macro_avg", {})
        logger.info(f"Macro avg: MAE={macro.get('mae', 'N/A'):.4f}, RMSE={macro.get('rmse', 'N/A'):.4f}, MAPE={macro.get('mape', 'N/A'):.2f}%")

        logger.info("Generating forecasts...")
        for entity_id, result in model_results.items():
            model = result["model"]
            fc = forecast_fn(model)
            last_date = entities[entity_id].index[-1]
            fc.index = pd.date_range(start=last_date, periods=len(fc) + 1, freq=config.RESAMPLE_FREQ)[1:]
            forecasts[entity_id] = fc

        if forecasts:
            forecast_concat = pd.concat(
                {k: v for k, v in forecasts.items()},
                names=["entity", "date"],
            ).reset_index(level=0)
            forecast_concat.to_csv(output_dir / "forecasts.csv", index=False)
            logger.info(f"Saved forecasts.csv ({len(forecasts)} entities)")

    residual_stats = {}
    for entity_id, df in entities.items():
        series = df[config.VALUE_COLUMN]
        try:
            residual_stats[entity_id] = compute_residual_stats(series)
        except Exception as e:
            logger.warning(f"Could not compute residual stats for {entity_id}: {e}")

    if residual_stats:
        stats_df = pd.DataFrame.from_dict(residual_stats, orient="index")
        stats_df.to_csv(output_dir / "residual_stats.csv")
        logger.info("Saved residual_stats.csv")

    logger.info("=" * 60)
    logger.info("Pipeline completed successfully!")
    logger.info(f"Results saved to {output_dir.resolve()}")
    logger.info("=" * 60)

    if args.dashboard:
        logger.info("Launching Streamlit dashboard...")
        import subprocess
        subprocess.run(["streamlit", "run", "src/dashboard.py"], check=True)


def main():
    args = parse_args()
    run(args)


if __name__ == "__main__":
    main()
