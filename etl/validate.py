"""
validate.py – Pydantic v2 data-quality validation.

Every row is validated through the ``Game`` model.  Rows that fail
validation are **not silently dropped**: they are captured with the
full raw record and the specific rejection reason, then stored in
the ``rejected_games`` table for auditing.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger(__name__)


# ── Pydantic v2 Game model ─────────────────────────────────────────────────


class Game(BaseModel):
    """Validated record for a single Steam game.

    All constraints are intentionally strict so that data quality
    issues surface immediately instead of poisoning downstream
    analysis or model training.
    """

    appid: int
    name: str = Field(min_length=1)
    release_date: date | None = None
    release_year: int = 0
    release_month: int = 0
    english: int = 1
    developer: str = "Unknown"
    publisher: str = "Unknown"

    # Pre-launch features
    price: float = Field(ge=0.0, default=0.0)
    is_free: int = 0
    required_age: int = Field(ge=0, default=0)
    achievements: int = Field(ge=0, default=0)
    is_windows: int = 0
    is_mac: int = 0
    is_linux: int = 0
    has_singleplayer: int = 0
    has_multiplayer: int = 0

    # Target
    owners: str = "0-0"
    owners_min: int = Field(ge=0, default=0)
    owners_max: int = Field(ge=0, default=0)
    owners_mid: float = Field(ge=0.0, default=0.0)
    popularity_tier: str = Field(pattern="^(Low|Medium|High)$", default="Low")

    # Post-launch outcomes (EDA only – DATA LEAKAGE if used as features)
    positive_ratings: int = Field(ge=0, default=0)
    negative_ratings: int = Field(ge=0, default=0)
    review_score: float = Field(ge=0.0, le=1.0, default=0.0)
    average_playtime: int = Field(ge=0, default=0)
    median_playtime: int = Field(ge=0, default=0)

    # Raw text fields
    platforms: str = "windows"
    categories: str = ""
    genres: str = ""
    steamspy_tags: str = ""

    # ── Validators ────────────────────────────────────────────────

    @field_validator("name", mode="before")
    @classmethod
    def name_must_be_non_empty(cls, v: Any) -> str:
        v = str(v).strip()
        if not v:
            raise ValueError("name must not be empty")
        return v

    @field_validator("release_date", mode="before")
    @classmethod
    def parse_release_date(cls, v: Any) -> date | None:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return None
        if isinstance(v, date):
            return v
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, pd.Timestamp):
            return v.date()
        try:
            return pd.to_datetime(str(v)).date()
        except Exception:
            return None

    @field_validator("owners", mode="before")
    @classmethod
    def validate_owners_range(cls, v: Any) -> str:
        """Ensure the owners field looks like ``"NNN-NNN"``."""
        text = str(v).replace(",", "").replace(" ", "")
        parts = text.split("-")
        if len(parts) != 2:
            parts = text.split("..")
        if len(parts) != 2:
            raise ValueError(f"Invalid owners range format: {v!r}")
        try:
            int(parts[0])
            int(parts[1])
        except ValueError:
            raise ValueError(f"Non-integer in owners range: {v!r}")
        return text

    @model_validator(mode="after")
    def check_owners_consistency(self) -> "Game":
        """owners_min must be <= owners_max."""
        if self.owners_min > self.owners_max:
            raise ValueError(
                f"owners_min ({self.owners_min}) > owners_max ({self.owners_max})"
            )
        return self


# ── Rejection record ──────────────────────────────────────────────────────


class RejectedGame(BaseModel):
    """A row that failed Pydantic validation, kept for audit."""
    appid: int | None = None
    raw_record: str      # JSON-encoded original row
    rejection_reason: str


# ── Batch validation ──────────────────────────────────────────────────────


def validate_dataframe(df: pd.DataFrame) -> tuple[list[dict], list[dict]]:
    """Validate every row in *df* through the ``Game`` model.

    Returns:
        A 2-tuple ``(valid_records, rejected_records)`` where each
        element is a list of plain dicts.

        * ``valid_records`` – dicts matching the ``Game`` schema.
        * ``rejected_records`` – dicts with keys ``appid``,
          ``raw_record`` (JSON string), and ``rejection_reason``.
    """
    valid: list[dict] = []
    rejected: list[dict] = []

    for idx, row in df.iterrows():
        raw_dict = row.to_dict()
        # Convert numpy/pandas types to native Python for JSON serialization
        for k, v in raw_dict.items():
            if isinstance(v, (pd.Timestamp,)):
                raw_dict[k] = str(v)
            elif hasattr(v, "item"):  # numpy scalar
                raw_dict[k] = v.item()

        try:
            game = Game(**raw_dict)
            valid.append(game.model_dump())
        except Exception as exc:
            appid = raw_dict.get("appid")
            reason = str(exc)
            logger.warning("Row %s (appid=%s) rejected: %s", idx, appid, reason)
            rejected.append(
                {
                    "appid": appid if appid is not None else -1,
                    "raw_record": json.dumps(raw_dict, default=str, ensure_ascii=False),
                    "rejection_reason": reason,
                }
            )

    logger.info("Validation complete: %d valid, %d rejected", len(valid), len(rejected))
    return valid, rejected
