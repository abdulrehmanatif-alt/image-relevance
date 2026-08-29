from fastapi import APIRouter

from app.schemas.image_matching import ImageMatchingRequest
from app.schemas.image_matching_response import ImageMatchingResponse
from app.services.image_matching_service import ImageMatchingService


router = APIRouter(
    prefix="/api/v1",
    tags=["Image Matching"],
)


service = ImageMatchingService()


@router.post("/match", response_model=ImageMatchingResponse)
def match_image(request: ImageMatchingRequest):
    return service.analyze(
        image_url=request.image_url,
        blog_content=request.blog_content,
    )


@router.get("/test")
def test_route():
    return {"message": "Image matching route is working"}