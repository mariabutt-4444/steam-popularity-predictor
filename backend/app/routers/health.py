from fastapi import APIRouter

router = APIRouter(tags=["Health"])

@router.get("/health")
def check_health():
    return {
        "status": "ok",
        "service": "Steam Game Popularity Predictor API",
        "stage": "Stage 1 (ETL + EDA)",
        "version": "1.0.0"
    }
