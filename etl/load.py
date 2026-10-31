"""
load.py – SQLAlchemy 2.0 persistence layer.

Defines the relational schema and bulk-load helpers for:
  • ``games``          – validated game records
  • ``genres``         – normalised genre lookup
  • ``game_genres``    – many-to-many bridge
  • ``rejected_games`` – validation failures with reasons
  • ``eda_tables``     – cached JSON EDA outputs
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    create_engine,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

from etl.config import DB_URL

logger = logging.getLogger(__name__)


# ── ORM base & engine ─────────────────────────────────────────────────────


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


# ── Association table ─────────────────────────────────────────────────────

game_genres = Table(
    "game_genres",
    Base.metadata,
    Column("game_appid", Integer, ForeignKey("games.appid", ondelete="CASCADE"), primary_key=True),
    Column("genre_id", Integer, ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
)


# ── ORM models ────────────────────────────────────────────────────────────


class GameModel(Base):
    """SQLAlchemy model for the ``games`` table."""

    __tablename__ = "games"

    appid = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    release_date = Column(String, nullable=True)  # ISO date string
    release_year = Column(Integer, nullable=False, default=0)
    release_month = Column(Integer, nullable=False, default=0)
    english = Column(Integer, nullable=False, default=1)
    developer = Column(Text, nullable=True)
    publisher = Column(Text, nullable=True)

    # Pre-launch features
    price = Column(Float, nullable=False, default=0.0)
    is_free = Column(Integer, nullable=False, default=0)
    required_age = Column(Integer, nullable=False, default=0)
    achievements = Column(Integer, nullable=False, default=0)
    is_windows = Column(Integer, nullable=False, default=1)
    is_mac = Column(Integer, nullable=False, default=0)
    is_linux = Column(Integer, nullable=False, default=0)
    has_singleplayer = Column(Integer, nullable=False, default=1)
    has_multiplayer = Column(Integer, nullable=False, default=0)

    # Target
    owners = Column(Text, nullable=False)
    owners_min = Column(Integer, nullable=False)
    owners_max = Column(Integer, nullable=False)
    owners_mid = Column(Float, nullable=False)
    popularity_tier = Column(Text, nullable=False)

    # Post-launch outcome fields [DATA LEAKAGE – EDA only]
    positive_ratings = Column(Integer, nullable=False, default=0)
    negative_ratings = Column(Integer, nullable=False, default=0)
    review_score = Column(Float, nullable=False, default=0.0)
    average_playtime = Column(Integer, nullable=False, default=0)
    median_playtime = Column(Integer, nullable=False, default=0)

    # Raw text
    platforms = Column(Text, nullable=True)
    categories = Column(Text, nullable=True)
    genres_raw = Column("genres", Text, nullable=True)
    steamspy_tags = Column(Text, nullable=True)

    # Relationships
    genres_rel = relationship("GenreModel", secondary=game_genres, back_populates="games")


class GenreModel(Base):
    """Normalised genre lookup table."""

    __tablename__ = "genres"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, unique=True, nullable=False)

    games = relationship("GameModel", secondary=game_genres, back_populates="genres_rel")


class RejectedGameModel(Base):
    """Dead-letter store for rows that failed Pydantic validation."""

    __tablename__ = "rejected_games"

    id = Column(Integer, primary_key=True, autoincrement=True)
    appid = Column(Integer, nullable=True)
    raw_record = Column(Text, nullable=False)
    rejection_reason = Column(Text, nullable=False)
    rejected_at = Column(DateTime, default=func.now())


class EdaTableModel(Base):
    """Cached EDA table output (JSON blobs)."""

    __tablename__ = "eda_tables"

    table_name = Column(Text, primary_key=True)
    insight_sentence = Column(Text, nullable=False)
    data_json = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


# ── Schema initialisation ─────────────────────────────────────────────────


def init_db() -> None:
    """Create all tables if they don't exist."""
    Base.metadata.create_all(engine)
    logger.info("Database tables created / verified at %s", DB_URL)


# ── Bulk loaders ──────────────────────────────────────────────────────────


def _get_or_create_genre(session: Session, name: str) -> GenreModel:
    """Return an existing ``GenreModel`` or create a new one."""
    genre = session.query(GenreModel).filter_by(name=name).first()
    if genre is None:
        genre = GenreModel(name=name)
        session.add(genre)
        session.flush()
    return genre


def load_games(valid_records: list[dict]) -> int:
    """Insert validated game dicts into the ``games`` and ``game_genres`` tables.

    Returns the number of rows inserted.
    """
    init_db()
    loaded = 0

    with SessionLocal() as session:
        # Clear previous data for idempotent reruns
        session.query(GameModel).delete()
        session.execute(game_genres.delete())
        session.query(GenreModel).delete()
        session.commit()

        for rec in valid_records:
            # Separate genre text before insertion
            genres_text: str = rec.get("genres", "")

            # Convert date objects to ISO strings for SQLite storage
            rd = rec.get("release_date")
            if isinstance(rd, (date, datetime)):
                rec["release_date"] = rd.isoformat()
            elif rd is None:
                rec["release_date"] = None

            game = GameModel(
                appid=rec["appid"],
                name=rec["name"],
                release_date=rec.get("release_date"),
                release_year=rec.get("release_year", 0),
                release_month=rec.get("release_month", 0),
                english=rec.get("english", 1),
                developer=rec.get("developer"),
                publisher=rec.get("publisher"),
                price=rec.get("price", 0.0),
                is_free=rec.get("is_free", 0),
                required_age=rec.get("required_age", 0),
                achievements=rec.get("achievements", 0),
                is_windows=rec.get("is_windows", 0),
                is_mac=rec.get("is_mac", 0),
                is_linux=rec.get("is_linux", 0),
                has_singleplayer=rec.get("has_singleplayer", 0),
                has_multiplayer=rec.get("has_multiplayer", 0),
                owners=rec.get("owners", "0-0"),
                owners_min=rec.get("owners_min", 0),
                owners_max=rec.get("owners_max", 0),
                owners_mid=rec.get("owners_mid", 0.0),
                popularity_tier=rec.get("popularity_tier", "Low"),
                positive_ratings=rec.get("positive_ratings", 0),
                negative_ratings=rec.get("negative_ratings", 0),
                review_score=rec.get("review_score", 0.0),
                average_playtime=rec.get("average_playtime", 0),
                median_playtime=rec.get("median_playtime", 0),
                platforms=rec.get("platforms"),
                genres_raw=genres_text,
                steamspy_tags=rec.get("steamspy_tags"),
                categories=rec.get("categories"),
            )
            session.add(game)

            # Normalise genres into the M2M table
            if genres_text:
                for gname in genres_text.split(";"):
                    gname = gname.strip()
                    if gname:
                        genre_obj = _get_or_create_genre(session, gname)
                        if genre_obj not in game.genres_rel:
                            game.genres_rel.append(genre_obj)

            loaded += 1

        session.commit()
        logger.info("Loaded %d games into database", loaded)

    return loaded


def load_rejected(rejected_records: list[dict]) -> int:
    """Insert rejected-row dicts into the ``rejected_games`` table.

    Returns the number of rows inserted.
    """
    init_db()

    with SessionLocal() as session:
        # Clear previous rejections for idempotent reruns
        session.query(RejectedGameModel).delete()
        session.commit()

        for rec in rejected_records:
            row = RejectedGameModel(
                appid=rec.get("appid"),
                raw_record=rec["raw_record"],
                rejection_reason=rec["rejection_reason"],
            )
            session.add(row)

        session.commit()
        count = len(rejected_records)
        logger.info("Loaded %d rejected rows into database", count)
        return count


def load_eda_table(table_name: str, insight: str, data: Any) -> None:
    """Upsert an EDA results table (as JSON) into the ``eda_tables`` cache."""
    init_db()

    with SessionLocal() as session:
        existing = session.query(EdaTableModel).filter_by(table_name=table_name).first()
        json_str = json.dumps(data, default=str, ensure_ascii=False)
        if existing:
            existing.insight_sentence = insight
            existing.data_json = json_str
        else:
            session.add(EdaTableModel(
                table_name=table_name,
                insight_sentence=insight,
                data_json=json_str,
            ))
        session.commit()
