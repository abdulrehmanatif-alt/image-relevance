from pydantic import BaseModel, Field


class ImageMatchingResponse(BaseModel):
    filename: str
    score: float = Field(..., ge=-1.0, le=1.0)
    accepted: bool
    explanation: str