from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class ReviewCreate(BaseModel):
    prompt_id: UUID
    reviewer_name: str
    score: int = Field(..., ge=1, le=5)
    feedback: str

class ReviewResponse(BaseModel):
    id: UUID
    prompt_id: UUID
    prompt_snapshot: str
    reviewer_name: str
    score: int
    feedback: str
    reviewed_at: datetime