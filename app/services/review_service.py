from app.schemas.review import ImageReviewRequest, ImageReviewResponse


class ReviewService:
    def __init__(self):
        self.reviews: dict[str, ImageReviewResponse] = {}

    def save_review(
        self,
        review: ImageReviewRequest,
    ) -> ImageReviewResponse:
        response = ImageReviewResponse(
            filename=review.filename,
            decision=review.decision,
            feedback=review.feedback,
        )

        self.reviews[review.filename] = response

        return response

    def get_review(self, filename: str) -> ImageReviewResponse | None:
        return self.reviews.get(filename)