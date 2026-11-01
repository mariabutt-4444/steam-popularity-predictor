from typing import List
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from backend.app.db import get_db
from backend.app.config import settings
from backend.app.schemas.pipeline import RejectedGameItem, PipelineRunResponse
from etl.load import RejectedGameModel
from etl.run_pipeline import run as run_etl_pipeline
from eda.analysis import run_eda

router = APIRouter(tags=["Pipeline"])

@router.get("/rejected", response_model=List[RejectedGameItem])
def get_rejected_rows(db: Session = Depends(get_db)):
    rows = db.query(RejectedGameModel).order_by(RejectedGameModel.id.desc()).all()
    return [
        RejectedGameItem(
            id=r.id,
            appid=r.appid,
            raw_record=r.raw_record,
            rejection_reason=r.rejection_reason,
            rejected_at=r.rejected_at.isoformat() if r.rejected_at else None,
        )
        for r in rows
    ]

@router.post("/pipeline/run", response_model=PipelineRunResponse)
def trigger_pipeline(
    x_api_key: str = Header(None, alias="X-API-Key"),
    source: str = "csv",
):
    if not x_api_key or x_api_key != settings.pipeline_api_key:
        raise HTTPException(status_code=403, detail="Invalid or missing X-API-Key header")
    try:
        metrics = run_etl_pipeline(source=source)
        run_eda()
        return PipelineRunResponse(status="success", metrics=metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")
