from app.services.embedding_service import EmbeddingService


class PostEmbeddingService:
    def __init__(self):
        self.embedding_service = EmbeddingService()

    def embed_post(self, text: str) -> list[float]:
        if not text.strip():
            raise ValueError("Post text cannot be empty.")

        return self.embedding_service.embed_text(text)