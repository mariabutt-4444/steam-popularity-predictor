from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.db import get_db
from backend.app.schemas.game import PaginatedGames, GameDetail
from backend.app.services.games_service import get_games, get_game_by_appid, get_all_genres

router = APIRouter(prefix="/games", tags=["Games"])

@router.get("", response_model=PaginatedGames)
def browse_games(
    search: Optional[str] = Query(None, description="Search by title, developer, or publisher"),
    genre: Optional[str] = Query(None, description="Filter by genre"),
    tier: Optional[str] = Query(None, description="Filter by popularity tier (Low, Medium, High)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return get_games(
        db=db,
        search=search,
        genre=genre,
        tier=tier,
        page=page,
        page_size=page_size,
    )

@router.get("/genres", response_model=List[str])
def list_genres(db: Session = Depends(get_db)):
    return get_all_genres(db)

@router.get("/{appid}", response_model=GameDetail)
def get_game(appid: int, db: Session = Depends(get_db)):
    game = get_game_by_appid(db, appid)
    if not game:
        raise HTTPException(status_code=404, detail=f"Game with appid {appid} not found")
    # Map genres_raw to genres for schema compatibility
    data = game.__dict__.copy()
    data["genres"] = game.genres_raw
    return data
