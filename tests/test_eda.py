"""
test_eda.py -- Unit tests for the Steam EDA module.

Uses tiny in-memory pandas DataFrames -- does NOT touch or depend on the real SQLite database.
Tests cover:
  1. Price-band binning edge cases
  2. Multi-label genre explode and count logic (including low-sample flag)
  3. IQR outlier detection function
  4. Popularity tier distribution summing to 100% and imbalance flag
  5. Missing-value table calculation and post-launch markers
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from eda.tables import (
    NUMERIC_COLS,
    POST_LAUNCH_FIELDS,
    assign_price_band,
    compute_iqr_outliers,
    genre_performance,
    missing_and_outliers,
    price_band_analysis,
    tier_distribution,
)


# ---------------------------------------------------------------------------
# Test Fixtures (tiny in-memory DataFrames)
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_games_df() -> pd.DataFrame:
    """Return a minimal synthetic games DataFrame with 10 rows."""
    return pd.DataFrame({
        "appid": list(range(1, 11)),
        "name": [f"Game {i}" for i in range(1, 11)],
        "price": [0.0, 2.99, 4.99, 5.0, 9.99, 14.99, 19.99, 29.99, 39.99, 49.99],
        "is_free": [1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "required_age": [0, 0, 0, 12, 0, 16, 0, 18, 0, 0],
        "achievements": [0, 5, 10, 20, 15, 30, 25, 50, 40, 100],
        "is_windows": [1] * 10,
        "is_mac": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
        "is_linux": [0, 0, 1, 0, 0, 1, 0, 0, 1, 0],
        "has_singleplayer": [1] * 10,
        "has_multiplayer": [0, 1, 0, 1, 0, 0, 1, 0, 1, 0],
        "owners": ["0-20000"] * 7 + ["20000-50000"] * 2 + ["200000-500000"],
        "owners_min": [0] * 7 + [20000] * 2 + [200000],
        "owners_max": [20000] * 7 + [50000] * 2 + [500000],
        "owners_mid": [10000.0] * 7 + [35000.0] * 2 + [350000.0],
        "popularity_tier": ["Low"] * 7 + ["Medium"] * 2 + ["High"] * 1,
        "positive_ratings": [10, 50, 100, 200, 500, 1000, 1500, 3000, 5000, 20000],
        "negative_ratings": [2, 10, 20, 40, 100, 200, 300, 500, 1000, 4000],
        "review_score": [0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8571, 0.8333, 0.8333],
        "average_playtime": [0, 60, 120, 180, 240, 300, 360, 420, 480, 1200],
        "median_playtime": [0, 60, 120, 180, 240, 300, 360, 420, 480, 1200],
        "release_year": [2015, 2016, 2016, 2017, 2017, 2018, 2018, 2018, 2019, 2019],
        "release_month": [1, 3, 5, 7, 9, 2, 4, 6, 8, 10],
    })


@pytest.fixture
def mock_genre_map() -> pd.DataFrame:
    """Return a synthetic genre map representing multi-label genres."""
    return pd.DataFrame({
        "appid": [1, 1, 2, 2, 2, 3, 4, 4, 5],
        "genre": ["Action", "Indie", "Action", "Adventure", "Indie", "Strategy", "Action", "RPG", "Indie"],
    })


# ---------------------------------------------------------------------------
# Test 1: Price-Band Binning Edges
# ---------------------------------------------------------------------------

def test_price_band_binning_edges():
    """Verify that exact price boundary values fall into the correct bins."""
    # Free band
    assert assign_price_band(0.0) == "Free"
    assert assign_price_band(-0.01) == "Free"

    # <$5 band: (0, 4.99]
    assert assign_price_band(0.01) == "<$5"
    assert assign_price_band(0.99) == "<$5"
    assert assign_price_band(4.99) == "<$5"

    # $5-10 band: (4.99, 9.99]
    assert assign_price_band(5.00) == "$5-10"
    assert assign_price_band(9.99) == "$5-10"

    # $10-20 band: (9.99, 19.99]
    assert assign_price_band(10.00) == "$10-20"
    assert assign_price_band(19.99) == "$10-20"

    # $20-40 band: (19.99, 39.99]
    assert assign_price_band(20.00) == "$20-40"
    assert assign_price_band(39.99) == "$20-40"

    # $40+ band: (39.99, inf)
    assert assign_price_band(40.00) == "$40+"
    assert assign_price_band(59.99) == "$40+"
    assert assign_price_band(199.99) == "$40+"


def test_price_band_analysis_output(mock_games_df):
    """Verify price_band_analysis returns non-empty records with expected bands."""
    result_df, insight = price_band_analysis(mock_games_df)
    assert isinstance(result_df, pd.DataFrame)
    assert isinstance(insight, str)
    assert len(insight) > 10

    # Ensure all 6 standard bands are recognized
    expected_bands = {"Free", "<$5", "$5-10", "$10-20", "$20-40", "$40+"}
    assert set(result_df["price_band"]).issubset(expected_bands)

    # Post-launch column must be explicitly marked in column name
    assert "avg_review_score_post_launch" in result_df.columns


# ---------------------------------------------------------------------------
# Test 2: Genre Explode and Count Logic
# ---------------------------------------------------------------------------

def test_genre_explode_and_count_logic(mock_games_df, mock_genre_map):
    """Verify multi-label genre explosion, aggregation, and low-sample flagging."""
    result_df, insight = genre_performance(mock_games_df, mock_genre_map)

    assert isinstance(result_df, pd.DataFrame)
    assert "genre" in result_df.columns
    assert "game_count" in result_df.columns
    assert "low_sample_flag" in result_df.columns
    assert "avg_review_score_post_launch" in result_df.columns

    # In mock_genre_map:
    # Action appears in appid 1, 2, 4 -> count = 3
    # Indie appears in appid 1, 2, 5 -> count = 3
    # Adventure appears in appid 2 -> count = 1
    # Strategy appears in appid 3 -> count = 1
    # RPG appears in appid 4 -> count = 1
    action_row = result_df[result_df["genre"] == "Action"]
    assert len(action_row) == 1
    assert int(action_row["game_count"].iloc[0]) == 3

    # All genres in mock have count < 10, so all must have low_sample_flag == True
    assert result_df["low_sample_flag"].all()


# ---------------------------------------------------------------------------
# Test 3: IQR Outlier Detection Function
# ---------------------------------------------------------------------------

def test_iqr_outlier_function():
    """Verify IQR fence calculations and outlier detection on a known distribution."""
    # Data with exactly one extreme outlier at 1000.0
    series = pd.Series([10.0, 11.0, 12.0, 12.0, 13.0, 14.0, 15.0, 15.0, 16.0, 1000.0])
    res = compute_iqr_outliers(series)

    assert "Q1" in res
    assert "Q3" in res
    assert "IQR" in res
    assert "lower_fence" in res
    assert "upper_fence" in res
    assert res["outlier_count"] == 1
    assert res["outlier_pct"] == 10.0  # 1 out of 10 = 10.0%

    # Clean data without outliers
    clean_series = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0, 15.0])
    clean_res = compute_iqr_outliers(clean_series)
    assert clean_res["outlier_count"] == 0
    assert clean_res["outlier_pct"] == 0.0


# ---------------------------------------------------------------------------
# Test 4: Popularity Tier Distribution Summing to 100%
# ---------------------------------------------------------------------------

def test_tier_distribution_sums_to_100(mock_games_df):
    """Verify popularity tier percentages sum to 100% and imbalance is flagged."""
    result_df, insight = tier_distribution(mock_games_df)

    assert isinstance(result_df, pd.DataFrame)
    assert len(result_df) == 3
    assert set(result_df["tier"]) == {"Low", "Medium", "High"}

    # Percentage sum must equal 100% (within roundoff tolerance)
    pct_sum = result_df["percentage"].sum()
    assert pytest.approx(pct_sum, rel=1e-3) == 100.0

    # Total counts must equal total rows
    total_count = result_df["count"].sum()
    assert total_count == len(mock_games_df)

    # In mock_games_df, Low=7, Medium=2, High=1 (7:1 ratio > 3:1 -> imbalanced)
    assert "is_imbalanced" in result_df.columns
    assert result_df["is_imbalanced"].iloc[0] is True or result_df["is_imbalanced"].iloc[0] == 1


# ---------------------------------------------------------------------------
# Test 5: Missing-Value Table & Post-Launch Field Markers
# ---------------------------------------------------------------------------

def test_missing_value_table():
    """Verify missing count calculation and post-launch metadata labeling."""
    # Create DataFrame with known missing values
    df = pd.DataFrame({
        "price": [1.99, np.nan, 4.99, 9.99],
        "required_age": [0, 0, 0, 0],
        "achievements": [10, 20, np.nan, 40],
        "owners_mid": [10000.0, 20000.0, 30000.0, 40000.0],
        "positive_ratings": [100, 200, 300, np.nan],
        "negative_ratings": [10, 20, 30, 40],
        "review_score": [0.9, 0.9, 0.9, 0.9],
        "average_playtime": [50, 100, 150, 200],
        "median_playtime": [50, 100, 150, 200],
    })

    result_df, insight = missing_and_outliers(df)

    assert isinstance(result_df, pd.DataFrame)
    assert len(result_df) == len(NUMERIC_COLS)

    # Verify missing counts
    price_row = result_df[result_df["field"] == "price"].iloc[0]
    assert price_row["missing_count"] == 1
    assert price_row["missing_pct"] == 25.0

    ach_row = result_df[result_df["field"] == "achievements"].iloc[0]
    assert ach_row["missing_count"] == 1

    pos_row = result_df[result_df["field"] == "positive_ratings"].iloc[0]
    assert pos_row["missing_count"] == 1

    # Verify is_post_launch flag on post-launch fields
    for field in POST_LAUNCH_FIELDS:
        row = result_df[result_df["field"] == field].iloc[0]
        assert bool(row["is_post_launch"]) is True, f"{field} must be flagged as is_post_launch"

    # Pre-launch fields must not be flagged
    assert bool(result_df[result_df["field"] == "price"].iloc[0]["is_post_launch"]) is False
    assert bool(result_df[result_df["field"] == "achievements"].iloc[0]["is_post_launch"]) is False
