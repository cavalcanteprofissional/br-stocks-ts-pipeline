import json
import logging
from pathlib import Path

import pandas as pd

from src.config import config
from src.outliers import compute_residual_stats, detect_anomaly_realtime

logger = logging.getLogger(__name__)


class AnomalyMonitor:
    def __init__(self, stats_dir: str | None = None):
        self.stats_dir = Path(stats_dir or config.OUTPUT_DIR)
        self.threshold_multiplier = config.ANOMALY_THRESHOLD
        self.stats: dict[str, dict] = {}
        self._load_stats()

    def _load_stats(self):
        stats_path = self.stats_dir / "residual_stats.csv"
        if stats_path.exists():
            df = pd.read_csv(stats_path, index_col=0)
            self.stats = df.to_dict(orient="index")
            logger.info(f"Loaded residual stats for {len(self.stats)} entities")
        else:
            logger.warning("No residual stats found. Run pipeline first.")

    def compute_and_save_stats(self, entities: dict[str, pd.DataFrame]):
        stats = {}
        for entity_id, df in entities.items():
            series = df[config.VALUE_COLUMN]
            try:
                stats[entity_id] = compute_residual_stats(series)
            except Exception as e:
                logger.warning(f"Failed to compute stats for {entity_id}: {e}")

        self.stats_dir.mkdir(parents=True, exist_ok=True)
        stats_df = pd.DataFrame.from_dict(stats, orient="index")
        stats_df.to_csv(self.stats_dir / "residual_stats.csv")
        self.stats = {k: v for k, v in stats.items()}
        logger.info(f"Saved residual stats for {len(self.stats)} entities")

    def check(self, entity_id: str, timestamp, value: float) -> dict:
        if entity_id not in self.stats:
            return {
                "is_anomaly": False,
                "residual": 0.0,
                "threshold": 0.0,
                "severity": "unknown",
                "error": f"No stats for entity {entity_id}",
            }

        stats = self.stats[entity_id]
        result = detect_anomaly_realtime(value, stats)
        result["entity_id"] = entity_id
        result["timestamp"] = str(timestamp)
        result["value"] = value
        return result

    def check_batch(self, observations: list[dict]) -> list[dict]:
        results = []
        for obs in observations:
            result = self.check(
                obs.get("entity_id"),
                obs.get("timestamp"),
                obs.get("value"),
            )
            results.append(result)
        return results
