from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, validator

class Review(BaseModel):
    id: Optional[UUID] = None
    restaurant_id: UUID
    user_id: Optional[UUID] = None
    review_text: str
    rating: Optional[float] = None
    review_hash: str
    source: str = "naver_map"
    created_at: Optional[datetime] = None

    @validator('rating')
    def validate_rating(cls, v):
        if v is not None and (v < 0 or v > 5):
            raise ValueError('Rating must be between 0 and 5')
        return v

    class Config:
        from_attributes = True