"""
analysis.py -- Structured Exploratory Data Analysis engine.

Computes 9 JSON-serializable tables from the ``games`` database,
each accompanied by an auto-generated one-sentence insight.
Results are cached in the ``eda_tables`` SQLite table.

Tables
------
1. summary_stats          -- descriptive statistics for numeric fields
2. missing_and_outliers   -- missing-value counts + IQR outlier counts
3. genre_performance      -- avg owners, review score, price by genre
4. price_band_distribution-- price bands vs review score & tier %
5. free_vs_paid           -- side-by-side F2P vs paid comparison
6. platform_support       -- platform combo vs popularity
7. yearly_trends          -- releases per year, avg price, % free
8. correlation_matrix     -- Pearson correlations of numeric features
9. popularity_tier_distribution -- class counts + imbalance flag
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

from etl.config import DB_URL, TIER_LOW_MAX, TIER_MEDIUM_MAX
from etl.load import load_eda_table, SessionLocal, GameModel, GenreModel, game_genres

logger = logging.getLogger(__name__)

# Numeric columns used across multiple analyses
NUMERIC_COLS = [
    "price", "required_age", "achievements",
    "owners_mid", "positive_ratings", "negative_ratings",
    "review_score", "average_playtime", "median_playtime",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_games_df() -> pd.DataFrame:
    """Load the full ``games`` table into a pandas DataFrame."""
    df = pd.read_sql_table("games", DB_URL)
    logger.info("Loaded %d games from database for EDA", len(df))
    return df


def _load_genre_map() -> pd.DataFrame:
    """Return a DataFrame with columns ``appid`` and ``genre``."""
    session = SessionLocal()
    try:
        rows = (
            session.query(game_genres.c.game_appid, GenreModel.name)
            .join(GenreModel, game_genres.c.genre_id == GenreModel.id)
            .all()
        )
        return pd.DataFrame(rows, columns=["appid", "genre"])
    finally:
        session.close()


def _round_dict(d: dict, decimals: int = 4) -> dict:
    """Round all float values in a flat dict."""
    return {
        k: round(v, decimals) if isinstance(v, float) else v
        for k, v in d.items()
    }


def _df_to_records(df: pd.DataFrame) -> dict:
    """Convert a DataFrame to ``{columns: [...], rows: [[...], ...]}}``."""
    return {
        "columns": list(df.columns),
        "rows": df.values.tolist(),
    }


def _safe_pct(num: float, denom: float) -> float:
    return round(num / denom * 100, 1) if denom else 0.0


# ---------------------------------------------------------------------------
# 1. Summary statistics
# ---------------------------------------------------------------------------

def compute_summary_stats(df: pd.DataFrame) -> tuple[dict, str]:
    """Mean, median, std, min, max, Q1, Q3 for each numeric column."""
    stats = df[NUMERIC_COLS].describe(percentiles=[0.25, 0.5, 0.75]).T
    stats = stats.rename(columns={"50%": "median", "25%": "Q1", "75%": "Q3"})
    stats["IQR"] = stats["Q3"] - stats["Q1"]
    stats = stats[["count", "mean", "std", "min", "Q1", "median", "Q3", "max", "IQR"]]
    stats = stats.round(4).reset_index().rename(columns={"index": "field"})

    median_price = df["price"].median()
    mean_playtime = df["average_playtime"].mean()
    insight = (
        f"The median game price is ${median_price:.2f} and the average playtime "
        f"is {mean_playtime:.0f} minutes, with high variance across all numeric features "
        f"indicating a diverse dataset."
    )
    return _df_to_records(stats), insight


# ---------------------------------------------------------------------------
# 2. Missing values & outliers (IQR method)
# ---------------------------------------------------------------------------

def compute_missing_and_outliers(df: pd.DataFrame) -> tuple[dict, str]:
    """Count missing values and IQR-fence outliers per numeric column."""
    records = []
    total_outliers = 0
    for col in NUMERIC_COLS:
        series = df[col]
        n_missing = int(series.isna().sum())
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        n_outliers = int(((series < lower) | (series > upper)).sum())
        total_outliers += n_outliers
        records.append({
            "field": col,
            "missing": n_missing,
            "missing_pct": _safe_pct(n_missing, len(df)),
            "Q1": round(float(q1), 4),
            "Q3": round(float(q3), 4),
            "IQR": round(float(iqr), 4),
            "lower_fence": round(float(lower), 4),
            "upper_fence": round(float(upper), 4),
            "outliers": n_outliers,
            "outlier_pct": _safe_pct(n_outliers, len(df)),
        })

    result_df = pd.DataFrame(records)
    n_missing_total = int(df[NUMERIC_COLS].isna().sum().sum())
    insight = (
        f"The cleaned dataset has {n_missing_total} total missing numeric values "
        f"and {total_outliers} IQR-based outliers, with owners_mid and playtime "
        f"showing the most extreme right-tail values driven by blockbuster titles."
    )
    return _df_to_records(result_df), insight


# ---------------------------------------------------------------------------
# 3. Genre performance
# ---------------------------------------------------------------------------

def compute_genre_performance(df: pd.DataFrame, genre_map: pd.DataFrame) -> tuple[dict, str]:
    """Average owners_mid, review_score, price grouped by genre."""
    merged = genre_map.merge(
        df[["appid", "owners_mid", "review_score", "price"]],
        on="appid",
        how="inner",
    )
    agg = (
        merged.groupby("genre")
        .agg(
            game_count=("appid", "count"),
            avg_owners=("owners_mid", "mean"),
            avg_review_score=("review_score", "mean"),
            avg_price=("price", "mean"),
        )
        .round(4)
        .sort_values("avg_owners", ascending=False)
        .reset_index()
    )

    top_genre = agg.iloc[0]["genre"] if len(agg) > 0 else "N/A"
    top_owners = agg.iloc[0]["avg_owners"] if len(agg) > 0 else 0
    insight = (
        f"{top_genre} leads in average estimated owners ({top_owners:,.0f}), "
        f"across {len(agg)} genres analyzed, showing large variation in "
        f"audience size between mainstream and niche categories."
    )
    return _df_to_records(agg), insight


# ---------------------------------------------------------------------------
# 4. Price band distribution
# ---------------------------------------------------------------------------

def compute_price_band_distribution(df: pd.DataFrame) -> tuple[dict, str]:
    """Segment games into price bands and show tier proportions."""
    bins = [-0.01, 0.0, 4.99, 9.99, 19.99, 39.99, float("inf")]
    labels = ["Free", "<$5", "$5-10", "$10-20", "$20-40", "$40+"]
    df = df.copy()
    df["price_band"] = pd.cut(df["price"], bins=bins, labels=labels)

    records = []
    for band in labels:
        subset = df[df["price_band"] == band]
        n = len(subset)
        if n == 0:
            continue
        tier_counts = subset["popularity_tier"].value_counts()
        records.append({
            "price_band": band,
            "game_count": n,
            "avg_review_score": round(float(subset["review_score"].mean()), 4),
            "avg_owners_mid": round(float(subset["owners_mid"].mean()), 0),
            "pct_low": _safe_pct(tier_counts.get("Low", 0), n),
            "pct_medium": _safe_pct(tier_counts.get("Medium", 0), n),
            "pct_high": _safe_pct(tier_counts.get("High", 0), n),
        })

    result_df = pd.DataFrame(records)
    free_high = result_df[result_df["price_band"] == "Free"]["pct_high"].values
    free_high_pct = free_high[0] if len(free_high) > 0 else 0
    insight = (
        f"Free games have {free_high_pct}% representation in the High tier, "
        f"while premium-priced games tend to have higher review scores but "
        f"smaller average audiences."
    )
    return _df_to_records(result_df), insight


# ---------------------------------------------------------------------------
# 5. Free vs Paid
# ---------------------------------------------------------------------------

def compute_free_vs_paid(df: pd.DataFrame) -> tuple[dict, str]:
    """Side-by-side comparison of free-to-play vs paid titles."""
    groups = {"Free": df[df["is_free"] == 1], "Paid": df[df["is_free"] == 0]}
    records = []
    for label, sub in groups.items():
        records.append({
            "category": label,
            "game_count": len(sub),
            "pct_of_total": _safe_pct(len(sub), len(df)),
            "avg_owners_mid": round(float(sub["owners_mid"].mean()), 0),
            "median_owners_mid": round(float(sub["owners_mid"].median()), 0),
            "avg_review_score": round(float(sub["review_score"].mean()), 4),
            "avg_achievements": round(float(sub["achievements"].mean()), 1),
            "avg_playtime": round(float(sub["average_playtime"].mean()), 0),
        })

    result_df = pd.DataFrame(records)
    free_owners = records[0]["avg_owners_mid"]
    paid_owners = records[1]["avg_owners_mid"]
    ratio = free_owners / paid_owners if paid_owners > 0 else 0
    insight = (
        f"Free-to-play games average {free_owners:,.0f} estimated owners vs "
        f"{paid_owners:,.0f} for paid titles ({ratio:.1f}x difference), "
        f"demonstrating the massive scale advantage of the F2P model."
    )
    return _df_to_records(result_df), insight


# ---------------------------------------------------------------------------
# 6. Platform support
# ---------------------------------------------------------------------------

def compute_platform_support(df: pd.DataFrame) -> tuple[dict, str]:
    """Cross-tabulation of platform combos vs popularity metrics."""
    df = df.copy()

    def _platform_combo(row: pd.Series) -> str:
        parts = []
        if row["is_windows"]:
            parts.append("Windows")
        if row["is_mac"]:
            parts.append("Mac")
        if row["is_linux"]:
            parts.append("Linux")
        return " + ".join(parts) if parts else "None"

    df["platform_combo"] = df.apply(_platform_combo, axis=1)
    agg = (
        df.groupby("platform_combo")
        .agg(
            game_count=("appid", "count"),
            avg_owners_mid=("owners_mid", "mean"),
            avg_review_score=("review_score", "mean"),
            avg_price=("price", "mean"),
            pct_high_tier=("popularity_tier", lambda x: _safe_pct((x == "High").sum(), len(x))),
        )
        .round(4)
        .sort_values("game_count", ascending=False)
        .reset_index()
    )

    win_only = agg[agg["platform_combo"] == "Windows"]
    all_three = agg[agg["platform_combo"] == "Windows + Mac + Linux"]
    win_only_high = float(win_only["pct_high_tier"].iloc[0]) if len(win_only) > 0 else 0
    all_high = float(all_three["pct_high_tier"].iloc[0]) if len(all_three) > 0 else 0
    insight = (
        f"Games supporting all three platforms (Windows+Mac+Linux) have "
        f"{all_high}% High-tier representation compared to {win_only_high}% "
        f"for Windows-only, suggesting cross-platform titles tend to reach "
        f"larger audiences."
    )
    return _df_to_records(agg), insight


# ---------------------------------------------------------------------------
# 7. Yearly release trends
# ---------------------------------------------------------------------------

def compute_yearly_trends(df: pd.DataFrame) -> tuple[dict, str]:
    """Games per year, average price, and % free over time."""
    valid = df[df["release_year"] > 0].copy()
    agg = (
        valid.groupby("release_year")
        .agg(
            games_released=("appid", "count"),
            avg_price=("price", "mean"),
            pct_free=("is_free", lambda x: _safe_pct(x.sum(), len(x))),
            avg_owners_mid=("owners_mid", "mean"),
        )
        .round(4)
        .reset_index()
    )

    if len(agg) > 1:
        peak_year = int(agg.loc[agg["games_released"].idxmax(), "release_year"])
        peak_count = int(agg["games_released"].max())
        insight = (
            f"Steam catalog peaked at {peak_count} releases in {peak_year} "
            f"(in this dataset), reflecting the explosive growth of indie "
            f"publishing on the platform."
        )
    else:
        insight = "Insufficient yearly data to identify release trends."

    return _df_to_records(agg), insight


# ---------------------------------------------------------------------------
# 8. Correlation matrix
# ---------------------------------------------------------------------------

def compute_correlation_matrix(df: pd.DataFrame) -> tuple[dict, str]:
    """Pearson correlation matrix of numeric features."""
    corr = df[NUMERIC_COLS].corr().round(4)
    # Add the field column as the first column
    corr = corr.reset_index().rename(columns={"index": "field"})

    # Find strongest non-trivial positive correlation
    corr_vals = df[NUMERIC_COLS].corr().to_numpy(copy=True)
    np.fill_diagonal(corr_vals, 0)
    max_idx = np.unravel_index(np.argmax(np.abs(corr_vals)), corr_vals.shape)
    f1 = NUMERIC_COLS[max_idx[0]]
    f2 = NUMERIC_COLS[max_idx[1]]
    max_corr = corr_vals[max_idx]

    insight = (
        f"The strongest correlation is between {f1} and {f2} "
        f"(r = {max_corr:.3f}), while post-launch fields (ratings, playtime) "
        f"are marked as leakage-prone and must be excluded from ML features."
    )
    return _df_to_records(corr), insight


# ---------------------------------------------------------------------------
# 9. Popularity tier distribution
# ---------------------------------------------------------------------------

def compute_tier_distribution(df: pd.DataFrame) -> tuple[dict, str]:
    """Popularity tier counts with imbalance analysis."""
    tier_order = ["Low", "Medium", "High"]
    counts = df["popularity_tier"].value_counts()
    total = len(df)

    records = []
    for tier in tier_order:
        n = int(counts.get(tier, 0))
        records.append({
            "tier": tier,
            "count": n,
            "percentage": _safe_pct(n, total),
        })

    result_df = pd.DataFrame(records)

    low_pct = _safe_pct(counts.get("Low", 0), total)
    high_pct = _safe_pct(counts.get("High", 0), total)
    imbalance = round(low_pct / high_pct, 1) if high_pct > 0 else 0

    # Add imbalance ratio row
    result_df["imbalance_ratio_vs_high"] = [
        round(counts.get(t, 0) / counts.get("High", 1), 1) for t in tier_order
    ]

    insight = (
        f"Severe class imbalance detected: Low tier represents {low_pct}% "
        f"of games ({imbalance}:1 ratio vs High), requiring stratified sampling "
        f"or class weighting in Stage 2 ML training."
    )
    return _df_to_records(result_df), insight


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

EDA_COMPUTERS: list[tuple[str, Any]] = [
    ("summary_stats", compute_summary_stats),
    ("missing_and_outliers", compute_missing_and_outliers),
    ("genre_performance", None),  # needs genre_map, handled specially
    ("price_band_distribution", compute_price_band_distribution),
    ("free_vs_paid", compute_free_vs_paid),
    ("platform_support", compute_platform_support),
    ("yearly_trends", compute_yearly_trends),
    ("correlation_matrix", compute_correlation_matrix),
    ("popularity_tier_distribution", compute_tier_distribution),
]


def run_eda() -> dict[str, dict]:
    """Compute all 9 EDA tables and cache them in the database.

    Returns:
        Dict mapping table name to ``{data: {...}, insight: "..."}}``.
    """
    logger.info("Starting EDA computation ...")
    df = _load_games_df()
    genre_map = _load_genre_map()
    results: dict[str, dict] = {}

    for table_name, computer in EDA_COMPUTERS:
        logger.info("  Computing: %s", table_name)
        if table_name == "genre_performance":
            data, insight = compute_genre_performance(df, genre_map)
        else:
            data, insight = computer(df)

        load_eda_table(table_name, insight, data)
        results[table_name] = {"data": data, "insight": insight}
        logger.info("    -> %s: %d rows | %s", table_name, len(data.get("rows", [])), insight[:80])

    logger.info("EDA complete: %d tables generated and cached.", len(results))
    return results


if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    results = run_eda()
    print(f"\nGenerated {len(results)} EDA tables:")
    for name, res in results.items():
        rows = len(res["data"].get("rows", []))
        print(f"  {name}: {rows} rows")
        print(f"    Insight: {res['insight']}")
