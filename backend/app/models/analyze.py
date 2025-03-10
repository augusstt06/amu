from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class Analyze(BaseModel):
    id: Optional[UUID] = None
    restaurant_id: UUID
    sentiment_score: float
    review_summary: str
    rating_reliability: float
    average_rating: float
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
