from typing import Optional, List
from pydantic import BaseModel

class GameBase(BaseModel):
    appid: int
    name: str
    release_date: Optional[str] = None
    release_year: int
    release_month: int
    english: int
    developer: Optional[str] = None
    publisher: Optional[str] = None
    price: float
    is_free: int
    required_age: int
    achievements: int
    is_windows: int
    is_mac: int
    is_linux: int
    has_singleplayer: int
    has_multiplayer: int
    owners: str
    owners_min: int
    owners_max: int
    owners_mid: float
    popularity_tier: str
    positive_ratings: int
    negative_ratings: int
    review_score: float
    average_playtime: int
    median_playtime: int
    platforms: Optional[str] = None
    categories: Optional[str] = None
    genres: Optional[str] = None
    steamspy_tags: Optional[str] = None

class GameDetail(GameBase):
    class Config:
        from_attributes = True

class GameListItem(BaseModel):
    appid: int
    name: str
    release_year: int
    price: float
    is_free: int
    popularity_tier: str
    review_score: float
    owners: str
    genres: Optional[str] = None
    platforms: Optional[str] = None

    class Config:
        from_attributes = True

class PaginatedGames(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[GameListItem]
