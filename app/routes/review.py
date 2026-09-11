from fastapi import APIRouter

from app.schemas.review import ImageReviewRequest, ImageReviewResponse
from app.services.review_service import ReviewService


router = APIRouter(
    prefix="/api/v1",
    tags=["Review"],
)


service = ReviewService()


@router.post("/review", response_model=ImageReviewResponse)
def submit_review(request: ImageReviewRequest):
    return service.save_review(request)


@router.get("/review/{filename}", response_model=ImageReviewResponse)
def get_review(filename: str):
    review = service.get_review(filename)

    if review is None:
        return {
            "filename": filename,
            "decision": "rejected",
            "feedback": "No review has been submitted for this image.",
        }

    return review