from enum import Enum

from pydantic import BaseModel, Field


class ReviewDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


class ImageReviewRequest(BaseModel):
    filename: str = Field(..., min_length=1)
    decision: ReviewDecision
    feedback: str = ""


class ImageReviewResponse(BaseModel):
    filename: str
    decision: ReviewDecision
    feedback: str