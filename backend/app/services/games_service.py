from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from etl.load import GameModel
from backend.app.schemas.game import PaginatedGames, GameListItem

def get_games(
    db: Session,
    search: Optional[str] = None,
    genre: Optional[str] = None,
    tier: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedGames:
    query = db.query(GameModel)

    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                GameModel.name.ilike(term),
                GameModel.developer.ilike(term),
                GameModel.publisher.ilike(term),
            )
        )

    if genre and genre.strip():
        query = query.filter(GameModel.genres_raw.ilike(f"%{genre.strip()}%"))

    if tier and tier.strip():
        query = query.filter(GameModel.popularity_tier == tier.strip())

    total = query.count()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    records = (
        query.order_by(GameModel.owners_mid.desc(), GameModel.positive_ratings.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [
        GameListItem(
            appid=r.appid,
            name=r.name,
            release_year=r.release_year,
            price=r.price,
            is_free=r.is_free,
            popularity_tier=r.popularity_tier,
            review_score=r.review_score,
            owners=r.owners,
            genres=r.genres_raw,
            platforms=r.platforms,
        )
        for r in records
    ]

    return PaginatedGames(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=items,
    )

def get_game_by_appid(db: Session, appid: int) -> Optional[GameModel]:
    return db.query(GameModel).filter(GameModel.appid == appid).first()

def get_all_genres(db: Session) -> List[str]:
    from etl.load import GenreModel
    genres = db.query(GenreModel.name).order_by(GenreModel.name).all()
    return [g[0] for g in genres]
