from typing import Optional, List, Dict
from pydantic import BaseModel

class RejectedGameItem(BaseModel):
    id: int
    appid: Optional[int]
    raw_record: str
    rejection_reason: str
    rejected_at: Optional[str]

    class Config:
        from_attributes = True

class PipelineRunResponse(BaseModel):
    status: str
    metrics: Dict[str, int]
