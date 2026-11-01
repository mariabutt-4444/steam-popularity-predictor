from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.db import get_db
from backend.app.schemas.stats import StatsIndexItem, StatsTableResponse
from backend.app.services.stats_service import get_stats_index, get_stats_table

router = APIRouter(prefix="/stats", tags=["Stats & EDA"])

@router.get("", response_model=List[StatsIndexItem])
def list_stats_tables(db: Session = Depends(get_db)):
    return get_stats_index(db)

@router.get("/{table_name}", response_model=StatsTableResponse)
def get_stats_table_data(table_name: str, db: Session = Depends(get_db)):
    table = get_stats_table(db, table_name)
    if not table:
        raise HTTPException(status_code=404, detail=f"EDA table '{table_name}' not found")
    return table
