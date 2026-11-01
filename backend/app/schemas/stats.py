from typing import List, Any
from pydantic import BaseModel

class StatsIndexItem(BaseModel):
    table_name: str
    insight: str

class StatsTableResponse(BaseModel):
    table_name: str
    insight: str
    columns: List[str]
    rows: List[List[Any]]
