from pydantic import BaseModel, Field


class ImageMatchingResponse(BaseModel):
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    explanation: str