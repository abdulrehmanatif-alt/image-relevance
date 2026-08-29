from pydantic import BaseModel, Field


class ImageMatchingRequest(BaseModel):
    image_url: str = Field(..., min_length=1)
    blog_content: str = Field(..., min_length=1)