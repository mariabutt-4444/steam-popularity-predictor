from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/predict", tags=["Prediction (Future Stage 2)"])

@router.post("")
@router.get("")
def predict_popularity():
    """Placeholder endpoint for Project 2 (scikit-learn Pipeline).

    Returns HTTP 501 Not Implemented as specified in the assignment roadmap.
    """
    raise HTTPException(
        status_code=501,
        detail="Coming in Project 2: Pre-launch game popularity prediction using scikit-learn Pipeline."
    )
