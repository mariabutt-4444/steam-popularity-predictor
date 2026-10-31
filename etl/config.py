"""
ETL configuration constants.

Centralises all tuneable knobs for the pipeline so that tier cut-offs,
rate-limit parameters and file paths can be changed in one place.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
API_CACHE_DIR = RAW_DIR / "api_cache"
CSV_PATH = RAW_DIR / "steam.csv"
DB_PATH = DATA_DIR / "steam.db"

# Ensure directories exist
API_CACHE_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Popularity-tier cut-offs  (owners_max boundaries)
# Expected distribution ≈ 69 % Low / 23 % Medium / 9 % High
# ---------------------------------------------------------------------------
TIER_LOW_MAX: int = 20_000        # owners_max <= this  → Low
TIER_MEDIUM_MAX: int = 200_000    # owners_max <= this  → Medium
                                  # owners_max > this   → High

# ---------------------------------------------------------------------------
# API rate-limiting
# ---------------------------------------------------------------------------
STEAMSPY_BULK_DELAY: float = 1.0        # seconds between bulk page requests
STEAMSPY_DETAIL_DELAY: float = 1.2      # seconds between appdetails requests
STORE_API_DELAY: float = 1.6            # ~200 req / 5 min ≈ 1.5 s each
MAX_RETRIES: int = 3
BACKOFF_FACTOR: float = 2.0             # exponential back-off multiplier

# ---------------------------------------------------------------------------
# Extraction targets
# ---------------------------------------------------------------------------
TARGET_SAMPLE_SIZE: int = 3_000         # min games to extract from APIs
MAX_SAMPLE_SIZE: int = 5_000            # hard upper cap

# ---------------------------------------------------------------------------
# SteamSpy API
# ---------------------------------------------------------------------------
STEAMSPY_BASE_URL: str = "https://steamspy.com/api.php"

# ---------------------------------------------------------------------------
# Steam Store API
# ---------------------------------------------------------------------------
STORE_BASE_URL: str = "https://store.steampowered.com/api/appdetails"

# ---------------------------------------------------------------------------
# Post-launch fields (DATA LEAKAGE – excluded from future ML features)
# ---------------------------------------------------------------------------
POST_LAUNCH_FIELDS: list[str] = [
    "positive_ratings",
    "negative_ratings",
    "review_score",
    "average_playtime",
    "median_playtime",
]

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DB_URL: str = f"sqlite:///{DB_PATH}"
