"""
extract.py – Data extraction layer.

Provides three data-source strategies:
  1. SteamSpy bulk + detail API  (throttled, cached, retried)
  2. Steam Store API             (throttled, cached, retried)
  3. CSV fallback reader         (data/raw/steam.csv)

Every raw API response is cached to disk so APIs are never re-called
unnecessarily.  If an API is unreachable the extractor automatically
falls back to the CSV.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from etl.config import (
    API_CACHE_DIR,
    BACKOFF_FACTOR,
    CSV_PATH,
    MAX_RETRIES,
    MAX_SAMPLE_SIZE,
    STEAMSPY_BASE_URL,
    STEAMSPY_BULK_DELAY,
    STEAMSPY_DETAIL_DELAY,
    STORE_API_DELAY,
    STORE_BASE_URL,
    TARGET_SAMPLE_SIZE,
)

logger = logging.getLogger(__name__)


# ── helpers ────────────────────────────────────────────────────────────────


def _cache_path(source: str, key: str) -> Path:
    """Return a deterministic file path for a cached response."""
    safe_key = str(key).replace("/", "_").replace("\\", "_")
    return API_CACHE_DIR / f"{source}_{safe_key}.json"


def _read_cache(source: str, key: str) -> dict | None:
    """Return cached JSON dict, or None if not cached."""
    path = _cache_path(source, key)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
    return None


def _write_cache(source: str, key: str, data: dict) -> None:
    """Persist a JSON dict to the cache directory."""
    path = _cache_path(source, key)
    try:
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except OSError as exc:
        logger.warning("Cache write failed for %s/%s: %s", source, key, exc)


def _request_with_retry(
    url: str,
    params: dict[str, Any] | None = None,
    max_retries: int = MAX_RETRIES,
    backoff: float = BACKOFF_FACTOR,
    timeout: int = 30,
) -> dict | None:
    """GET *url* with exponential back-off.  Returns parsed JSON or None."""
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            wait = backoff ** attempt
            logger.warning(
                "Request %s attempt %d/%d failed (%s) – retrying in %.1fs",
                url,
                attempt,
                max_retries,
                exc,
                wait,
            )
            time.sleep(wait)
    logger.error("All %d retries exhausted for %s", max_retries, url)
    return None


# ── SteamSpy ───────────────────────────────────────────────────────────────


def _fetch_steamspy_bulk(pages: int = 5) -> dict[int, dict]:
    """Fetch bulk game listings from SteamSpy (``request=all&page=N``).

    Returns a dict keyed by *appid* containing the summary records.
    """
    all_games: dict[int, dict] = {}
    for page in range(pages):
        cache_key = f"bulk_page_{page}"
        cached = _read_cache("steamspy", cache_key)
        if cached is not None:
            logger.info("SteamSpy bulk page %d: loaded from cache (%d items)", page, len(cached))
            for appid_str, record in cached.items():
                all_games[int(appid_str)] = record
            continue

        logger.info("SteamSpy bulk page %d: fetching from API …", page)
        data = _request_with_retry(
            STEAMSPY_BASE_URL,
            params={"request": "all", "page": str(page)},
        )
        if data is None:
            logger.error("SteamSpy bulk page %d failed – aborting bulk fetch.", page)
            break

        _write_cache("steamspy", cache_key, data)
        for appid_str, record in data.items():
            all_games[int(appid_str)] = record

        logger.info("SteamSpy bulk page %d: received %d items (total %d)", page, len(data), len(all_games))
        time.sleep(STEAMSPY_BULK_DELAY)

    return all_games


def _fetch_steamspy_details(appids: list[int]) -> dict[int, dict]:
    """Fetch per-app detail from SteamSpy for each *appid*."""
    details: dict[int, dict] = {}
    for i, appid in enumerate(appids):
        cache_key = f"detail_{appid}"
        cached = _read_cache("steamspy", cache_key)
        if cached is not None:
            details[appid] = cached
            continue

        data = _request_with_retry(
            STEAMSPY_BASE_URL,
            params={"request": "appdetails", "appid": str(appid)},
        )
        if data:
            _write_cache("steamspy", cache_key, data)
            details[appid] = data

        if (i + 1) % 100 == 0:
            logger.info("SteamSpy details: %d / %d fetched", i + 1, len(appids))
        time.sleep(STEAMSPY_DETAIL_DELAY)

    return details


# ── Steam Store ────────────────────────────────────────────────────────────


def _fetch_store_details(appids: list[int]) -> dict[int, dict]:
    """Fetch store details for each *appid* from the Steam Store API."""
    details: dict[int, dict] = {}
    for i, appid in enumerate(appids):
        cache_key = f"store_{appid}"
        cached = _read_cache("store", cache_key)
        if cached is not None:
            details[appid] = cached
            continue

        data = _request_with_retry(
            STORE_BASE_URL,
            params={"appids": str(appid)},
        )
        if data and str(appid) in data:
            entry = data[str(appid)]
            if entry.get("success"):
                _write_cache("store", cache_key, entry.get("data", {}))
                details[appid] = entry.get("data", {})

        if (i + 1) % 50 == 0:
            logger.info("Store API details: %d / %d fetched", i + 1, len(appids))
        time.sleep(STORE_API_DELAY)

    return details


# ── CSV reader ─────────────────────────────────────────────────────────────


def extract_csv(csv_path: Path | None = None) -> pd.DataFrame:
    """Read the Kaggle-format CSV into a DataFrame.

    Args:
        csv_path: Override for the default ``data/raw/steam.csv``.

    Returns:
        Raw DataFrame with all original columns.
    """
    path = csv_path or CSV_PATH
    logger.info("Reading CSV fallback from %s", path)
    df = pd.read_csv(path, encoding="utf-8")
    logger.info("CSV loaded: %d rows, %d columns", len(df), len(df.columns))
    return df


# ── API extraction (merges SteamSpy + Store) ───────────────────────────────


def extract_api() -> pd.DataFrame:
    """Run the full API extraction pipeline.

    1. Bulk-fetch game summaries from SteamSpy.
    2. Sample up to ``TARGET_SAMPLE_SIZE`` … ``MAX_SAMPLE_SIZE`` appids.
    3. Fetch per-app detail from SteamSpy and Steam Store.
    4. Merge the three sources on *appid*.

    Falls back to the CSV if SteamSpy bulk returns nothing.
    """
    bulk = _fetch_steamspy_bulk(pages=5)
    if not bulk:
        logger.warning("SteamSpy bulk returned 0 records – falling back to CSV.")
        return extract_csv()

    # Sample appids
    appids = list(bulk.keys())[:MAX_SAMPLE_SIZE]
    if len(appids) > TARGET_SAMPLE_SIZE:
        appids = appids[:TARGET_SAMPLE_SIZE]
    logger.info("Selected %d appids for detail fetch", len(appids))

    spy_details = _fetch_steamspy_details(appids)
    store_details = _fetch_store_details(appids)

    # Build unified rows matching CSV schema
    rows: list[dict] = []
    for appid in appids:
        spy_bulk = bulk.get(appid, {})
        spy_det = spy_details.get(appid, {})
        store = store_details.get(appid, {})

        # Prefer SteamSpy detail, fall back to bulk
        merged = {**spy_bulk, **spy_det}

        # Extract store fields
        price_overview = store.get("price_overview", {})
        platforms_store = store.get("platforms", {})
        genres_store = store.get("genres", [])
        categories_store = store.get("categories", [])

        platforms_parts: list[str] = []
        if platforms_store.get("windows"):
            platforms_parts.append("windows")
        if platforms_store.get("mac"):
            platforms_parts.append("mac")
        if platforms_store.get("linux"):
            platforms_parts.append("linux")

        genre_names = [g.get("description", "") for g in genres_store] if isinstance(genres_store, list) else []
        cat_names = [c.get("description", "") for c in categories_store] if isinstance(categories_store, list) else []

        row = {
            "appid": appid,
            "name": merged.get("name", store.get("name", "")),
            "release_date": store.get("release_date", {}).get("date", ""),
            "english": 1,
            "developer": ";".join(store.get("developers", [])) if isinstance(store.get("developers"), list) else merged.get("developer", ""),
            "publisher": ";".join(store.get("publishers", [])) if isinstance(store.get("publishers"), list) else merged.get("publisher", ""),
            "platforms": ";".join(platforms_parts) if platforms_parts else merged.get("platforms", "windows"),
            "required_age": store.get("required_age", 0),
            "categories": ";".join(cat_names) if cat_names else "",
            "genres": ";".join(genre_names) if genre_names else merged.get("genre", ""),
            "steamspy_tags": merged.get("tags", ""),
            "achievements": store.get("achievements", {}).get("total", 0) if isinstance(store.get("achievements"), dict) else merged.get("achievements", 0),
            "positive_ratings": merged.get("positive", 0),
            "negative_ratings": merged.get("negative", 0),
            "average_playtime": merged.get("average_forever", 0),
            "median_playtime": merged.get("median_forever", 0),
            "owners": merged.get("owners", "0-0"),
            "price": (price_overview.get("initial", 0) / 100.0) if price_overview else merged.get("price", 0),
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    logger.info("API extraction complete: %d rows", len(df))
    return df


# ── Public entry point ─────────────────────────────────────────────────────


def extract(source: str = "csv") -> pd.DataFrame:
    """Main extraction dispatcher.

    Args:
        source: ``"api"`` to use SteamSpy + Steam Store with CSV fallback,
                ``"csv"`` to use the Kaggle CSV directly.

    Returns:
        Raw DataFrame ready for transformation.
    """
    if source == "api":
        try:
            return extract_api()
        except Exception:
            logger.exception("API extraction failed – falling back to CSV")
            return extract_csv()
    return extract_csv()
