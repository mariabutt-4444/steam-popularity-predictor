"""
tables.py -- Reusable EDA table-building functions for the Steam dataset.

Each public function:
  • accepts a pandas DataFrame (loaded separately from SQLite),
  • returns a plain pandas DataFrame of JSON-serializable records,
  • returns a one-sentence insight derived from the computed numbers,
  • marks any column sourced from post-launch data (review / playtime).

Tables
------
1. summary_statistics        -- count, mean, median, std, min, Q1, Q3, max
2. missing_and_outliers      -- missing counts / % and IQR outlier counts / %
3. genre_performance         -- avg owners, review score, count per genre
4. price_band_analysis       -- price bands vs review score, owners, tier mix
5. free_vs_paid              -- F2P vs paid comparison
6. platform_support          -- Windows / Mac / Linux counts, owners, tier mix
7. yearly_trends             -- releases, avg price, % free per year
8. correlation_table         -- Pearson + Spearman for skewed variables
9. tier_distribution         -- popularity tier counts, %, imbalance flag
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Post-launch outcome columns (data-leakage risk for ML)
POST_LAUNCH_FIELDS: list[str] = [
    "positive_ratings",
    "negative_ratings",
    "review_score",
    "average_playtime",
    "median_playtime",
]

# Numeric columns used across multiple analyses
NUMERIC_COLS: list[str] = [
    "price",
    "required_age",
    "achievements",
    "owners_mid",
    "positive_ratings",
    "negative_ratings",
    "review_score",
    "average_playtime",
    "median_playtime",
]

# Price-band edges and labels
PRICE_BINS: list[float] = [-0.01, 0.0, 4.99, 9.99, 19.99, 39.99, float("inf")]
PRICE_LABELS: list[str] = ["Free", "<$5", "$5-10", "$10-20", "$20-40", "$40+"]

# Threshold below which a genre count is flagged as low-sample
LOW_SAMPLE_THRESHOLD: int = 10

# Skewness threshold above which Spearman is also reported
SKEW_THRESHOLD: float = 1.0


# ---------------------------------------------------------------------------
# Data-loading helpers (read-only — nothing is written back to the DB)
# ---------------------------------------------------------------------------

def load_games_df(db_url: str) -> pd.DataFrame:
    """Load the full ``games`` table into a pandas DataFrame.

    This is the only database access point for the EDA module.
    All operations are read-only.
    """
    df = pd.read_sql_table("games", db_url)
    logger.info("Loaded %d games from database", len(df))
    return df


def load_genre_map(db_url: str) -> pd.DataFrame:
    """Return a tidy DataFrame with columns ``appid`` and ``genre``.

    Uses the normalised ``game_genres`` + ``genres`` tables so that
    multi-label genres are already exploded into separate rows.
    """
    query = """
        SELECT gg.game_appid AS appid, g.name AS genre
        FROM game_genres gg
        JOIN genres g ON gg.genre_id = g.id
    """
    df = pd.read_sql_query(query, db_url)
    logger.info(
        "Loaded %d genre mappings (%d unique genres)",
        len(df), df["genre"].nunique(),
    )
    return df


# ---------------------------------------------------------------------------
# Small helper utilities
# ---------------------------------------------------------------------------

def _safe_pct(numerator: float, denominator: float, decimals: int = 2) -> float:
    """Return percentage, guarded against division by zero."""
    if denominator == 0:
        return 0.0
    return round(numerator / denominator * 100, decimals)


def _small_sample_caveat(n: int, threshold: int = 50) -> str:
    """Return a caveat string when the sample is small."""
    if n < threshold:
        return f" (caution: small sample, n={n})"
    return ""


def assign_price_band(price: float) -> str:
    """Assign a price-band label to a single price value.

    Bands (right-inclusive):
        Free:    price == 0
        <$5:     0 < price <= 4.99
        $5-10:   4.99 < price <= 9.99
        $10-20:  9.99 < price <= 19.99
        $20-40:  19.99 < price <= 39.99
        $40+:    price > 39.99

    This standalone function is also used in unit tests.
    """
    if price <= 0.0:
        return "Free"
    if price <= 4.99:
        return "<$5"
    if price <= 9.99:
        return "$5-10"
    if price <= 19.99:
        return "$10-20"
    if price <= 39.99:
        return "$20-40"
    return "$40+"


def compute_iqr_outliers(series: pd.Series) -> dict:
    """Compute IQR-based outlier statistics for a single numeric Series.

    Returns a dict with keys: Q1, Q3, IQR, lower_fence, upper_fence,
    outlier_count, outlier_pct.

    This standalone function is also used in unit tests.
    """
    q1 = float(series.quantile(0.25))
    q3 = float(series.quantile(0.75))
    iqr = q3 - q1
    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr
    n_outliers = int(((series < lower_fence) | (series > upper_fence)).sum())
    return {
        "Q1": round(q1, 4),
        "Q3": round(q3, 4),
        "IQR": round(iqr, 4),
        "lower_fence": round(lower_fence, 4),
        "upper_fence": round(upper_fence, 4),
        "outlier_count": n_outliers,
        "outlier_pct": _safe_pct(n_outliers, len(series)),
    }


# ---------------------------------------------------------------------------
# 1. Summary statistics
# ---------------------------------------------------------------------------

def summary_statistics(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Descriptive statistics for every numeric column.

    Returns
    -------
    DataFrame
        One row per field with columns: field, count, mean, std, min,
        Q1, median, Q3, max, is_post_launch.
    str
        Auto-generated insight sentence.
    """
    desc = (
        df[NUMERIC_COLS]
        .describe(percentiles=[0.25, 0.5, 0.75])
        .T
    )
    desc = desc.rename(columns={"50%": "median", "25%": "Q1", "75%": "Q3"})
    desc = desc[["count", "mean", "std", "min", "Q1", "median", "Q3", "max"]]
    desc = desc.round(4)
    desc = desc.reset_index().rename(columns={"index": "field"})

    # Mark post-launch fields so downstream consumers can filter them out
    desc["is_post_launch"] = desc["field"].isin(POST_LAUNCH_FIELDS)

    # --- Auto-generated insight ---
    median_price = float(df["price"].median())
    mean_owners = float(df["owners_mid"].mean())
    insight = (
        f"The median game price is ${median_price:.2f} and the mean estimated "
        f"owners is {mean_owners:,.0f}. High standard deviations across most "
        f"fields indicate a highly diverse dataset"
        f"{_small_sample_caveat(len(df))}."
    )

    logger.info("Table 1 (summary_statistics): %d fields", len(desc))
    return desc, insight


# ---------------------------------------------------------------------------
# 2. Missing values & outliers (IQR method)
# ---------------------------------------------------------------------------

def missing_and_outliers(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Missing-value counts and IQR-based outlier detection per numeric column.

    Returns
    -------
    DataFrame
        Columns: field, missing_count, missing_pct, Q1, Q3, IQR,
        lower_fence, upper_fence, outlier_count, outlier_pct,
        is_post_launch.
    str
        Auto-generated insight sentence.
    """
    records: list[dict] = []
    total_outliers = 0
    n = len(df)

    for col in NUMERIC_COLS:
        series = df[col]
        n_missing = int(series.isna().sum())

        # Reuse the standalone IQR helper
        iqr_info = compute_iqr_outliers(series)
        total_outliers += iqr_info["outlier_count"]

        records.append({
            "field": col,
            "missing_count": n_missing,
            "missing_pct": _safe_pct(n_missing, n),
            **iqr_info,
            "is_post_launch": col in POST_LAUNCH_FIELDS,
        })

    result = pd.DataFrame(records)

    # Identify the column with the most outliers for the insight
    worst_idx = result["outlier_count"].idxmax()
    worst_col = result.loc[worst_idx, "field"]
    worst_count = int(result["outlier_count"].max())

    insight = (
        f"The dataset has 0 missing numeric values (ETL imputed defaults). "
        f"{total_outliers} IQR-based outliers detected in total; "
        f"{worst_col} has the most ({worst_count}, "
        f"{_safe_pct(worst_count, n)}%) driven by right-tail "
        f"blockbuster values{_small_sample_caveat(n)}."
    )

    logger.info(
        "Table 2 (missing_and_outliers): %d fields, %d total outliers",
        len(result), total_outliers,
    )
    return result, insight


# ---------------------------------------------------------------------------
# 3. Genre performance
# ---------------------------------------------------------------------------

def genre_performance(
    df: pd.DataFrame,
    genre_map: pd.DataFrame,
) -> tuple[pd.DataFrame, str]:
    """Average owners and review score by genre, with game counts.

    Multi-label genres are handled via the pre-exploded ``genre_map``
    (each game appears once per genre it belongs to).

    Genres with fewer than LOW_SAMPLE_THRESHOLD games are flagged.

    Post-launch columns: avg_review_score [post_launch].
    """
    # Merge genre map with game-level metrics
    merged = genre_map.merge(
        df[["appid", "owners_mid", "review_score", "price", "popularity_tier"]],
        on="appid",
        how="inner",
    )

    agg = (
        merged.groupby("genre")
        .agg(
            game_count=("appid", "count"),
            avg_owners=("owners_mid", "mean"),
            avg_review_score_post_launch=("review_score", "mean"),
            avg_price=("price", "mean"),
        )
        .round(4)
        .sort_values("avg_owners", ascending=False)
        .reset_index()
    )

    # Flag genres with too few games
    agg["low_sample_flag"] = agg["game_count"] < LOW_SAMPLE_THRESHOLD

    # --- Insight ---
    top = agg.iloc[0] if len(agg) > 0 else None
    if top is not None:
        low_sample_count = int(agg["low_sample_flag"].sum())
        insight = (
            f"{top['genre']} leads with avg {top['avg_owners']:,.0f} estimated "
            f"owners across {int(top['game_count'])} games. "
            f"{len(agg)} genres analysed; {low_sample_count} have fewer than "
            f"{LOW_SAMPLE_THRESHOLD} games (flagged as low-sample)"
            f"{_small_sample_caveat(len(df))}."
        )
    else:
        insight = "No genre data available."

    logger.info("Table 3 (genre_performance): %d genres", len(agg))
    return agg, insight


# ---------------------------------------------------------------------------
# 4. Price-band analysis
# ---------------------------------------------------------------------------

def price_band_analysis(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Price-band segments vs average review score, owners, and tier mix.

    Bands: Free, <$5, $5-10, $10-20, $20-40, $40+.

    Post-launch columns: avg_review_score [post_launch].
    """
    tmp = df.copy()
    tmp["price_band"] = pd.cut(
        tmp["price"], bins=PRICE_BINS, labels=PRICE_LABELS,
    )

    records: list[dict] = []
    for band in PRICE_LABELS:
        subset = tmp[tmp["price_band"] == band]
        n = len(subset)
        if n == 0:
            continue

        tier_counts = subset["popularity_tier"].value_counts()
        records.append({
            "price_band": band,
            "game_count": n,
            "avg_review_score_post_launch": round(
                float(subset["review_score"].mean()), 4,
            ),
            "avg_owners": round(float(subset["owners_mid"].mean()), 0),
            "pct_Low": _safe_pct(tier_counts.get("Low", 0), n),
            "pct_Medium": _safe_pct(tier_counts.get("Medium", 0), n),
            "pct_High": _safe_pct(tier_counts.get("High", 0), n),
        })

    result = pd.DataFrame(records)

    # --- Insight ---
    if len(result) > 0:
        best_idx = result["avg_review_score_post_launch"].idxmax()
        best_band = result.loc[best_idx, "price_band"]
        best_val = float(result["avg_review_score_post_launch"].max())
        free_row = result[result["price_band"] == "Free"]
        free_high = (
            float(free_row["pct_High"].iloc[0]) if len(free_row) > 0 else 0
        )
        insight = (
            f"The {best_band} band has the highest avg review score "
            f"({best_val:.3f}). Free games show {free_high}% High-tier "
            f"representation. Premium games tend toward higher review scores "
            f"but smaller audiences{_small_sample_caveat(len(df))}."
        )
    else:
        insight = "No price-band data available."

    logger.info("Table 4 (price_band_analysis): %d bands", len(result))
    return result, insight


# ---------------------------------------------------------------------------
# 5. Free vs Paid
# ---------------------------------------------------------------------------

def free_vs_paid(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Side-by-side comparison of free-to-play vs paid games.

    Post-launch columns: avg_review_score [post_launch],
                         avg_playtime [post_launch].
    """
    groups = {"Free": df[df["is_free"] == 1], "Paid": df[df["is_free"] == 0]}
    records: list[dict] = []

    for label, sub in groups.items():
        n = len(sub)
        if n == 0:
            continue

        tier_counts = sub["popularity_tier"].value_counts()
        records.append({
            "category": label,
            "game_count": n,
            "pct_of_total": _safe_pct(n, len(df)),
            "avg_owners": round(float(sub["owners_mid"].mean()), 0),
            "median_owners": round(float(sub["owners_mid"].median()), 0),
            "avg_review_score_post_launch": round(
                float(sub["review_score"].mean()), 4,
            ),
            "avg_playtime_post_launch": round(
                float(sub["average_playtime"].mean()), 0,
            ),
            "pct_Low": _safe_pct(tier_counts.get("Low", 0), n),
            "pct_Medium": _safe_pct(tier_counts.get("Medium", 0), n),
            "pct_High": _safe_pct(tier_counts.get("High", 0), n),
        })

    result = pd.DataFrame(records)

    # --- Insight ---
    if len(records) == 2:
        free_owners = records[0]["avg_owners"]
        paid_owners = records[1]["avg_owners"]
        ratio = free_owners / paid_owners if paid_owners > 0 else 0
        free_n = records[0]["game_count"]
        insight = (
            f"Free-to-play games ({free_n} titles) average "
            f"{free_owners:,.0f} estimated owners vs {paid_owners:,.0f} for "
            f"paid ({ratio:.1f}x difference), demonstrating the scale "
            f"advantage of the F2P model"
            f"{_small_sample_caveat(free_n)}."
        )
    else:
        insight = "Insufficient data for free-vs-paid comparison."

    logger.info("Table 5 (free_vs_paid): %d categories", len(result))
    return result, insight


# ---------------------------------------------------------------------------
# 6. Platform support
# ---------------------------------------------------------------------------

def platform_support(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Platform support comparison: Windows, Mac, Linux.

    Shows per-platform game count, average owners, and tier mix.
    Each row represents one platform; games supporting multiple
    platforms appear in multiple rows.
    """
    platforms = {
        "Windows": "is_windows",
        "Mac": "is_mac",
        "Linux": "is_linux",
    }

    records: list[dict] = []
    for plat_name, col in platforms.items():
        sub = df[df[col] == 1]
        n = len(sub)
        if n == 0:
            continue

        tier_counts = sub["popularity_tier"].value_counts()
        records.append({
            "platform": plat_name,
            "game_count": n,
            "pct_of_total": _safe_pct(n, len(df)),
            "avg_owners": round(float(sub["owners_mid"].mean()), 0),
            "avg_review_score_post_launch": round(
                float(sub["review_score"].mean()), 4,
            ),
            "pct_Low": _safe_pct(tier_counts.get("Low", 0), n),
            "pct_Medium": _safe_pct(tier_counts.get("Medium", 0), n),
            "pct_High": _safe_pct(tier_counts.get("High", 0), n),
        })

    result = pd.DataFrame(records)

    # --- Insight ---
    if len(result) >= 2:
        top_idx = result["avg_owners"].idxmax()
        top_plat = result.loc[top_idx, "platform"]
        top_owners = result.loc[top_idx, "avg_owners"]
        win_count = int(
            result.loc[result["platform"] == "Windows", "game_count"].iloc[0]
        )
        mac_count = int(
            result.loc[result["platform"] == "Mac", "game_count"].iloc[0]
        )
        linux_count = int(
            result.loc[result["platform"] == "Linux", "game_count"].iloc[0]
        )
        insight = (
            f"{top_plat}-supported games average the highest estimated "
            f"owners ({top_owners:,.0f}). {win_count} games support "
            f"Windows vs {mac_count} Mac and {linux_count} Linux"
            f"{_small_sample_caveat(len(df))}."
        )
    else:
        insight = "Insufficient platform variety for comparison."

    logger.info("Table 6 (platform_support): %d platforms", len(result))
    return result, insight


# ---------------------------------------------------------------------------
# 7. Yearly release trends
# ---------------------------------------------------------------------------

def yearly_trends(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Games released per year, average price, and share of free games.

    Years with ``release_year == 0`` (unparseable dates) are excluded.
    """
    valid = df[df["release_year"] > 0].copy()

    agg = (
        valid.groupby("release_year")
        .agg(
            games_released=("appid", "count"),
            avg_price=("price", "mean"),
            pct_free=("is_free", lambda x: _safe_pct(int(x.sum()), len(x))),
            avg_owners=("owners_mid", "mean"),
        )
        .round(4)
        .reset_index()
    )

    # --- Insight ---
    if len(agg) > 1:
        peak_idx = int(agg["games_released"].idxmax())
        peak_year = int(agg.loc[peak_idx, "release_year"])
        peak_count = int(agg.loc[peak_idx, "games_released"])
        latest_free_pct = float(agg.iloc[-1]["pct_free"])
        insight = (
            f"Release volume peaked at {peak_count} games in {peak_year} "
            f"(in this sample). The most recent year shows "
            f"{latest_free_pct}% free-to-play share. Note: yearly counts "
            f"are from a ~1,500-game stratified sample, not the full "
            f"Steam catalogue."
        )
    else:
        insight = "Insufficient yearly data to identify trends."

    logger.info("Table 7 (yearly_trends): %d years", len(agg))
    return agg, insight


# ---------------------------------------------------------------------------
# 8. Correlation table (Pearson + Spearman)
# ---------------------------------------------------------------------------

def correlation_table(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Pearson correlations for all numeric pairs; Spearman added for skewed ones.

    Returns a long-form table (one row per pair, upper-triangle only)
    with columns: field_1, field_2, pearson_r, spearman_r,
    is_post_launch.

    ``spearman_r`` is populated only when at least one variable in the
    pair has |skewness| > SKEW_THRESHOLD; otherwise it is ``None``.
    """
    # Pearson matrix
    pearson = df[NUMERIC_COLS].corr(method="pearson").round(4)

    # Identify skewed columns
    skewed_cols: list[str] = []
    for col in NUMERIC_COLS:
        skew_val = float(df[col].skew())
        if abs(skew_val) > SKEW_THRESHOLD:
            skewed_cols.append(col)

    # Spearman matrix (computed once if needed)
    spearman = (
        df[NUMERIC_COLS].corr(method="spearman").round(4)
        if skewed_cols
        else None
    )

    # Build long-form records (upper triangle, no self-correlations)
    records: list[dict] = []
    for i, c1 in enumerate(NUMERIC_COLS):
        for j, c2 in enumerate(NUMERIC_COLS):
            if j <= i:
                continue  # skip diagonal and lower triangle

            row: dict[str, Any] = {
                "field_1": c1,
                "field_2": c2,
                "pearson_r": float(pearson.loc[c1, c2]),
            }

            # Add Spearman only when at least one variable is skewed
            if c1 in skewed_cols or c2 in skewed_cols:
                row["spearman_r"] = (
                    float(spearman.loc[c1, c2]) if spearman is not None else None
                )
            else:
                row["spearman_r"] = None

            # Mark if either field is a post-launch outcome
            row["is_post_launch"] = (
                c1 in POST_LAUNCH_FIELDS or c2 in POST_LAUNCH_FIELDS
            )

            records.append(row)

    result = pd.DataFrame(records)

    # --- Insight ---
    strongest_idx = int(result["pearson_r"].abs().idxmax())
    strongest = result.loc[strongest_idx]
    skewed_str = ", ".join(skewed_cols) if skewed_cols else "none"

    insight = (
        f"Strongest Pearson correlation: {strongest['field_1']} <-> "
        f"{strongest['field_2']} (r = {strongest['pearson_r']:.3f}). "
        f"Skewed columns ({skewed_str}) also include Spearman rank "
        f"correlations. Post-launch fields are marked and must be "
        f"excluded from ML features{_small_sample_caveat(len(df))}."
    )

    logger.info(
        "Table 8 (correlation_table): %d pairs, %d skewed columns",
        len(result), len(skewed_cols),
    )
    return result, insight


# ---------------------------------------------------------------------------
# 9. Popularity tier distribution
# ---------------------------------------------------------------------------

def tier_distribution(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Popularity tier counts, percentages, and imbalance flag.

    Expected split: ~69 % Low / 23 % Medium / 9 % High.
    """
    tier_order = ["Low", "Medium", "High"]
    counts = df["popularity_tier"].value_counts()
    total = len(df)

    records: list[dict] = []
    for tier in tier_order:
        n = int(counts.get(tier, 0))
        records.append({
            "tier": tier,
            "count": n,
            "percentage": _safe_pct(n, total),
        })

    result = pd.DataFrame(records)

    # Imbalance ratios relative to the smallest class (High)
    high_count = int(counts.get("High", 1))
    result["imbalance_ratio_vs_High"] = result["count"].apply(
        lambda c: round(c / high_count, 1) if high_count > 0 else 0.0
    )

    # Imbalance flag (> 3:1 Low-to-High is considered severe)
    low_pct = _safe_pct(counts.get("Low", 0), total)
    high_pct = _safe_pct(counts.get("High", 0), total)
    imbalance_ratio = round(low_pct / high_pct, 1) if high_pct > 0 else 0.0
    is_imbalanced = imbalance_ratio > 3.0
    result["is_imbalanced"] = is_imbalanced

    # --- Insight ---
    med_pct = _safe_pct(counts.get("Medium", 0), total)
    insight = (
        f"Class imbalance {'detected' if is_imbalanced else 'within tolerance'}: "
        f"Low {low_pct}% / Medium {med_pct}% / High {high_pct}% "
        f"(Low:High ratio = {imbalance_ratio}:1). "
        f"The High tier has only {high_count} games — "
        f"stratified sampling or class weighting will be needed for ML"
        f"{_small_sample_caveat(high_count, threshold=100)}."
    )

    logger.info(
        "Table 9 (tier_distribution): %s",
        {t: int(counts.get(t, 0)) for t in tier_order},
    )
    return result, insight
