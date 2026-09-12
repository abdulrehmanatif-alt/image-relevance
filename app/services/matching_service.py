from sqlalchemy import select

from app.database import SessionLocal
from app.models import Image

from app.services.post_embedding_service import PostEmbeddingService
from app.services.similarity_service import cosine_similarity
from app.services.mismatch_guard import MismatchGuard


class MatchingService:
    def __init__(self):
        self.post_embedding_service = PostEmbeddingService()
        self.mismatch_guard = MismatchGuard()

        with SessionLocal() as db:
            images = db.scalars(
                select(Image).where(
                    Image.embedding.is_not(None)
                )
            ).all()

            self.image_embeddings = [
                {
                    "filename": image.filename,
                    "embedding": image.embedding,
                }
                for image in images
            ]

            self.image_metadata = {
                image.filename: {
                    "subject": image.subject or "",
		    "category": image.category or "",
		    "confidence": image.confidence if image.confidence is not None else 0.0,
                }
                for image in images
            }

    def rank_images(self, post_text: str) -> list[dict]:
        post_embedding = self.post_embedding_service.embed_post(post_text)

        results = []

        for image in self.image_embeddings:
            score = cosine_similarity(
                post_embedding,
                image["embedding"],
            )

            metadata = self.image_metadata.get(image["filename"])

            if metadata:
                guard_result = self.mismatch_guard.check(
                    similarity=score,
                    image_subject=metadata.get("subject", ""),
                    image_category=metadata.get("category", ""),
                    image_confidence=metadata.get("confidence", 0.0),
                    post_text=post_text,
                )

                results.append(
                    {
                        "filename": image["filename"],
                        "score": score,
                        "accepted": guard_result.accepted,
                        "reason": guard_result.reason,
                    }
                )
            else:
                results.append(
                    {
                        "filename": image["filename"],
                        "score": score,
                        "accepted": False,
                        "reason": "Image metadata is unavailable.",
                    }
                )

        results.sort(
        key=lambda item: (item["accepted"], item["score"]),
        reverse=True,
        )

        return results