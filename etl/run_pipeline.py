"""
run_pipeline.py -- CLI entry-point for the ETL pipeline.

Usage::

    python -m etl.run_pipeline --source csv
    python -m etl.run_pipeline --source api

Prints row counts at every stage:
  extracted -> transformed -> valid / rejected -> loaded
"""

from __future__ import annotations

import argparse
import logging
import sys
import time

from etl.extract import extract
from etl.transform import transform
from etl.validate import validate_dataframe
from etl.load import load_games, load_rejected, init_db


def _configure_logging(verbose: bool = False) -> None:
    """Set up structured console logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def run(source: str = "csv", verbose: bool = False) -> dict:
    """Execute the full ETL pipeline and return stage metrics.

    Args:
        source: ``"api"`` or ``"csv"``.
        verbose: enable DEBUG-level logging.

    Returns:
        Dict with keys ``extracted``, ``transformed``, ``valid``,
        ``rejected``, ``loaded``.
    """
    _configure_logging(verbose)
    logger = logging.getLogger("etl.pipeline")
    logger.info("===================================================")
    logger.info("  Steam Game Popularity Predictor -- ETL Pipeline")
    logger.info("  Source: %s", source.upper())
    logger.info("===================================================")

    t0 = time.time()
    metrics: dict[str, int] = {}

    # -- Stage 1: Extract --
    logger.info("[STAGE 1] Extract")
    df_raw = extract(source=source)
    metrics["extracted"] = len(df_raw)
    logger.info("  -> Extracted: %d rows", metrics["extracted"])

    # -- Stage 2: Transform --
    logger.info("[STAGE 2] Transform")
    df_clean = transform(df_raw)
    metrics["transformed"] = len(df_clean)
    logger.info("  -> Transformed: %d rows", metrics["transformed"])

    # -- Stage 3: Validate --
    logger.info("[STAGE 3] Validate (Pydantic v2)")
    valid_records, rejected_records = validate_dataframe(df_clean)
    metrics["valid"] = len(valid_records)
    metrics["rejected"] = len(rejected_records)
    logger.info("  -> Valid: %d  |  Rejected: %d", metrics["valid"], metrics["rejected"])

    # -- Stage 4: Load --
    logger.info("[STAGE 4] Load (SQLAlchemy -> SQLite)")
    init_db()
    loaded = load_games(valid_records)
    rejected_loaded = load_rejected(rejected_records)
    metrics["loaded"] = loaded
    metrics["rejected_loaded"] = rejected_loaded
    logger.info("  -> Loaded: %d games  |  %d rejected rows", loaded, rejected_loaded)

    # -- Summary --
    elapsed = time.time() - t0
    logger.info("===================================================")
    logger.info("  Pipeline complete in %.1f seconds", elapsed)
    logger.info("  Extracted:   %d", metrics["extracted"])
    logger.info("  Transformed: %d", metrics["transformed"])
    logger.info("  Valid:       %d", metrics["valid"])
    logger.info("  Rejected:    %d", metrics["rejected"])
    logger.info("  Loaded:      %d", metrics["loaded"])
    logger.info("===================================================")

    return metrics


def main() -> None:
    """CLI argument parser and dispatcher."""
    parser = argparse.ArgumentParser(
        description="Steam Game Popularity Predictor -- ETL Pipeline",
    )
    parser.add_argument(
        "--source",
        choices=["api", "csv"],
        default="csv",
        help="Data source: 'api' for SteamSpy+Store with CSV fallback, "
             "'csv' for the Kaggle CSV directly (default: csv)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable DEBUG-level logging",
    )
    args = parser.parse_args()
    run(source=args.source, verbose=args.verbose)


if __name__ == "__main__":
    main()
