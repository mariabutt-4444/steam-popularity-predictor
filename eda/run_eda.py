"""
run_eda.py -- CLI entry-point that builds all 9 EDA tables and exports them.

Usage::

    python -m eda.run_eda                           # defaults to data/steam.db
    python -m eda.run_eda --db-url sqlite:///other.db

Output is saved to ``eda/output/`` as both CSV and JSON files.
Nothing is written back to the database.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

from eda.tables import (
    load_games_df,
    load_genre_map,
    summary_statistics,
    missing_and_outliers,
    genre_performance,
    price_band_analysis,
    free_vs_paid,
    platform_support,
    yearly_trends,
    correlation_table,
    tier_distribution,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_DB_URL = f"sqlite:///{_PROJECT_ROOT / 'data' / 'steam.db'}"
_OUTPUT_DIR = _PROJECT_ROOT / "eda" / "output"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _save_table(
    name: str,
    df: pd.DataFrame,
    insight: str,
    output_dir: Path,
) -> None:
    """Save a single EDA table as CSV and JSON.

    Args:
        name:       Filename stem (e.g. ``"01_summary_statistics"``).
        df:         DataFrame to export.
        insight:    One-sentence auto-generated insight.
        output_dir: Folder to write into (created if needed).
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # --- CSV ---
    csv_path = output_dir / f"{name}.csv"
    df.to_csv(csv_path, index=False)
    logger.info("  Saved CSV:  %s", csv_path)

    # --- JSON (records format + insight metadata) ---
    json_path = output_dir / f"{name}.json"
    payload = {
        "table_name": name,
        "insight": insight,
        "row_count": len(df),
        "columns": list(df.columns),
        "data": json.loads(
            df.to_json(orient="records", default_handler=str)
        ),
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str, ensure_ascii=False)
    logger.info("  Saved JSON: %s", json_path)


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def run_all_tables(db_url: str | None = None) -> dict[str, dict]:
    """Compute and export all 9 EDA tables.

    Args:
        db_url: SQLAlchemy database URL.  Defaults to the project DB.

    Returns:
        Dict mapping table_name -> {"data": DataFrame, "insight": str}.
    """
    db_url = db_url or _DEFAULT_DB_URL

    logger.info("=" * 60)
    logger.info("  Steam EDA -- Building all tables")
    logger.info("  Database : %s", db_url)
    logger.info("  Output   : %s", _OUTPUT_DIR)
    logger.info("=" * 60)

    # Load data once (read-only)
    df = load_games_df(db_url)
    genre_map = load_genre_map(db_url)

    # Table registry: (file_stem, function, extra keyword args)
    table_registry: list[tuple[str, object, dict]] = [
        ("01_summary_statistics",    summary_statistics,    {}),
        ("02_missing_and_outliers",  missing_and_outliers,  {}),
        ("03_genre_performance",     genre_performance,     {"genre_map": genre_map}),
        ("04_price_band_analysis",   price_band_analysis,   {}),
        ("05_free_vs_paid",          free_vs_paid,          {}),
        ("06_platform_support",      platform_support,      {}),
        ("07_yearly_trends",         yearly_trends,         {}),
        ("08_correlation_table",     correlation_table,     {}),
        ("09_tier_distribution",     tier_distribution,     {}),
    ]

    results: dict[str, dict] = {}

    for name, func, extra in table_registry:
        logger.info("Computing: %s", name)
        result_df, insight = func(df, **extra)
        _save_table(name, result_df, insight, _OUTPUT_DIR)
        results[name] = {"data": result_df, "insight": insight}
        logger.info(
            "  -> %d rows | %s", len(result_df), insight[:90],
        )

    logger.info("=" * 60)
    logger.info(
        "  EDA complete: %d tables saved to %s", len(results), _OUTPUT_DIR,
    )
    logger.info("=" * 60)

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    """Parse arguments and run all EDA tables."""
    parser = argparse.ArgumentParser(
        description="Steam Game Popularity Predictor -- EDA Table Builder",
    )
    parser.add_argument(
        "--db-url",
        default=None,
        help=f"SQLAlchemy DB URL (default: {_DEFAULT_DB_URL})",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable DEBUG-level logging",
    )
    args = parser.parse_args()

    # Configure logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    results = run_all_tables(db_url=args.db_url)

    # Print a human-friendly summary
    print(f"\n{'=' * 60}")
    print(f"Generated {len(results)} EDA tables -> eda/output/")
    print(f"{'=' * 60}")
    for name, res in results.items():
        n_rows = len(res["data"])
        print(f"  {name}: {n_rows} rows")
        print(f"    Insight: {res['insight']}")
    print()


if __name__ == "__main__":
    main()
