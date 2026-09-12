from sqlalchemy import select

from app.database import SessionLocal
from app.models import Review
from app.schemas.review import ImageReviewRequest, ImageReviewResponse


class ReviewService:
    def save_review(
        self,
        review: ImageReviewRequest,
    ) -> ImageReviewResponse:
        with SessionLocal() as db:
            existing = db.scalar(
                select(Review).where(
                    Review.filename == review.filename
                )
            )

            if existing:
                existing.decision = review.decision
                existing.feedback = review.feedback
            else:
                db.add(
                    Review(
                        filename=review.filename,
                        decision=review.decision,
                        feedback=review.feedback,
                    )
                )

            db.commit()

            return ImageReviewResponse(
                filename=review.filename,
                decision=review.decision,
                feedback=review.feedback,
            )

    def get_review(
        self,
        filename: str,
    ) -> ImageReviewResponse | None:
        with SessionLocal() as db:
            review = db.scalar(
                select(Review).where(
                    Review.filename == filename
                )
            )

            if not review:
                return None

            return ImageReviewResponse(
                filename=review.filename,
                decision=review.decision,
                feedback=review.feedback,
            )