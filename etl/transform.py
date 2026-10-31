"""
transform.py – Pandas-based data transformation.

Responsibilities:
  • Parse ``owners`` range string → owners_min, owners_max, owners_mid
  • Derive ``popularity_tier`` with configurable cut-offs
  • Parse dates → release_year, release_month
  • Split semicolon-separated fields into binary flags
  • Compute review_score with division-by-zero guard
  • Handle missing values and remove duplicate appids
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

from etl.config import POST_LAUNCH_FIELDS, TIER_LOW_MAX, TIER_MEDIUM_MAX

logger = logging.getLogger(__name__)


# ── Owners parsing ─────────────────────────────────────────────────────────


def parse_owners(owners_str: Any) -> tuple[int, int, float]:
    """Parse an owners range string like ``"20000-50000"`` into (min, max, mid).

    Returns ``(0, 0, 0.0)`` for un-parseable values.
    """
    if pd.isna(owners_str):
        return 0, 0, 0.0
    text = str(owners_str).replace(",", "").replace(" ", "")
    parts = text.split("-")
    if len(parts) != 2:
        # Try ".." separator that SteamSpy sometimes uses
        parts = text.split("..")
    if len(parts) != 2:
        logger.debug("Unparseable owners string: %r", owners_str)
        return 0, 0, 0.0
    try:
        lo, hi = int(parts[0]), int(parts[1])
        return lo, hi, (lo + hi) / 2.0
    except (ValueError, TypeError):
        return 0, 0, 0.0


def assign_tier(owners_max: int) -> str:
    """Map *owners_max* to a popularity tier label.

    Tier boundaries are imported from ``etl.config``:
      - Low:    owners_max <= 20 000
      - Medium: 20 000 < owners_max <= 200 000
      - High:   owners_max > 200 000
    """
    if owners_max <= TIER_LOW_MAX:
        return "Low"
    if owners_max <= TIER_MEDIUM_MAX:
        return "Medium"
    return "High"


# ── Main transform function ───────────────────────────────────────────────


def transform(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all cleaning and feature-engineering steps.

    Args:
        df: Raw DataFrame straight from the extraction stage.

    Returns:
        Cleaned DataFrame with derived columns, ready for validation.
    """
    logger.info("Transform: starting with %d rows", len(df))
    initial_count = len(df)

    # ── 1. Drop duplicate appids ──────────────────────────────────────
    df = df.drop_duplicates(subset="appid", keep="first").copy()
    dupes_removed = initial_count - len(df)
    if dupes_removed:
        logger.info("Removed %d duplicate appid rows", dupes_removed)

    # ── 2. Parse owners range ─────────────────────────────────────────
    parsed = df["owners"].apply(parse_owners)
    df["owners_min"] = parsed.apply(lambda t: t[0])
    df["owners_max"] = parsed.apply(lambda t: t[1])
    df["owners_mid"] = parsed.apply(lambda t: t[2])

    # ── 3. Popularity tier ────────────────────────────────────────────
    df["popularity_tier"] = df["owners_max"].apply(assign_tier)
    tier_counts = df["popularity_tier"].value_counts()
    tier_pct = df["popularity_tier"].value_counts(normalize=True).mul(100).round(1)
    logger.info(
        "Tier distribution — %s",
        ", ".join(f"{t}: {tier_counts[t]} ({tier_pct[t]}%%)" for t in ["Low", "Medium", "High"] if t in tier_counts.index),
    )

    # ── 4. Date parsing ───────────────────────────────────────────────
    df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")
    df["release_year"] = df["release_date"].dt.year.fillna(0).astype(int)
    df["release_month"] = df["release_date"].dt.month.fillna(0).astype(int)

    # ── 5. Handle missing / default values ────────────────────────────
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0.0)
    df["required_age"] = pd.to_numeric(df["required_age"], errors="coerce").fillna(0).astype(int)
    df["achievements"] = pd.to_numeric(df["achievements"], errors="coerce").fillna(0).astype(int)
    df["positive_ratings"] = pd.to_numeric(df["positive_ratings"], errors="coerce").fillna(0).astype(int)
    df["negative_ratings"] = pd.to_numeric(df["negative_ratings"], errors="coerce").fillna(0).astype(int)
    df["average_playtime"] = pd.to_numeric(df["average_playtime"], errors="coerce").fillna(0).astype(int)
    df["median_playtime"] = pd.to_numeric(df["median_playtime"], errors="coerce").fillna(0).astype(int)
    df["english"] = pd.to_numeric(df["english"], errors="coerce").fillna(1).astype(int)

    # Fill missing text fields
    df["name"] = df["name"].fillna("").astype(str)
    df["developer"] = df["developer"].fillna("Unknown")
    df["publisher"] = df["publisher"].fillna("Unknown")
    df["platforms"] = df["platforms"].fillna("windows")
    df["categories"] = df["categories"].fillna("")
    df["genres"] = df["genres"].fillna("")
    df["steamspy_tags"] = df["steamspy_tags"].fillna("")

    # ── 6. Platform / category binary flags ───────────────────────────
    platforms_lower = df["platforms"].str.lower()
    df["is_windows"] = platforms_lower.str.contains("windows", na=False).astype(int)
    df["is_mac"] = platforms_lower.str.contains("mac", na=False).astype(int)
    df["is_linux"] = platforms_lower.str.contains("linux", na=False).astype(int)

    df["is_free"] = (df["price"] == 0).astype(int)

    categories_lower = df["categories"].str.lower()
    df["has_multiplayer"] = categories_lower.str.contains("multi-player", na=False).astype(int)
    df["has_singleplayer"] = categories_lower.str.contains("single-player", na=False).astype(int)

    # ── 7. Review score (guarded div-by-zero) ─────────────────────────
    total_ratings = df["positive_ratings"] + df["negative_ratings"]
    df["review_score"] = np.where(
        total_ratings > 0,
        df["positive_ratings"] / total_ratings,
        0.0,
    )
    df["review_score"] = df["review_score"].round(4)

    # ── 8. Mark post-launch fields in metadata ───────────────────────
    #    (This is documentation / schema-level; the columns stay in the
    #     DataFrame but ``POST_LAUNCH_FIELDS`` from config.py lists them
    #     so downstream stages can exclude them.)
    logger.info(
        "Post-launch outcome fields (EDA only, excluded from future ML): %s",
        POST_LAUNCH_FIELDS,
    )

    # ── Logging summary ──────────────────────────────────────────────
    logger.info(
        "Transform complete: %d rows, %d columns",
        len(df),
        len(df.columns),
    )
    return df
