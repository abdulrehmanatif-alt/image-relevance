import json
from pathlib import Path

from app.services.post_embedding_service import PostEmbeddingService
from app.services.similarity_service import cosine_similarity
from app.services.mismatch_guard import MismatchGuard


EMBEDDINGS_FILE = Path("data/image_embeddings.json")
DATASET_FILE = Path("data/dataset.json")


class MatchingService:
    def __init__(self):
        self.post_embedding_service = PostEmbeddingService()
        self.mismatch_guard = MismatchGuard()

        with open(EMBEDDINGS_FILE, "r", encoding="utf-8") as file:
            self.image_embeddings = json.load(file)

        with open(DATASET_FILE, "r", encoding="utf-8") as file:
            dataset = json.load(file)

        self.image_metadata = {
            image["filename"]: image
            for image in dataset["images"]
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