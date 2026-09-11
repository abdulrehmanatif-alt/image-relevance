from pydantic import BaseModel, Field


class ImageMatchingRequest(BaseModel):
    blog_content: str = Field(..., min_length=1)