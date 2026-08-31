from enum import Enum

from pydantic import BaseModel, Field


class ImageCategory(str, Enum):
    ANIMAL = "animal"
    VEHICLE = "vehicle"
    LANDSCAPE = "landscape"
    OBJECT = "object"
    PERSON = "person"
    ILLUSTRATION = "illustration"


class ImageUnderstanding(BaseModel):
    subject: str = Field(..., min_length=1)
    category: ImageCategory
    attributes: list[str] = Field(default_factory=list)
    caption: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)