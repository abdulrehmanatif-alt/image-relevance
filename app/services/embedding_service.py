from google import genai

from app.config import settings


class EmbeddingService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.llm_api_key)
        self.model = settings.embedding_model

    def embed_text(self, text: str) -> list[float]:
        response = self.client.models.embed_content(
            model=self.model,
            contents=text,
            config={
                "output_dimensionality": 768,
            },
        )

        return response.embeddings[0].values