import json
from pathlib import Path

from app.services.post_embedding_service import PostEmbeddingService
from app.services.similarity_service import cosine_similarity


EMBEDDINGS_FILE = Path("data/image_embeddings.json")


class MatchingService:
    def __init__(self):
        self.post_embedding_service = PostEmbeddingService()

        with open(EMBEDDINGS_FILE, "r", encoding="utf-8") as file:
            self.image_embeddings = json.load(file)

    def rank_images(self, post_text: str) -> list[dict]:
        post_embedding = self.post_embedding_service.embed_post(post_text)

        results = []

        for image in self.image_embeddings:
            score = cosine_similarity(
                post_embedding,
                image["embedding"],
            )

            results.append(
                {
                    "filename": image["filename"],
                    "score": score,
                }
            )

        results.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        return results