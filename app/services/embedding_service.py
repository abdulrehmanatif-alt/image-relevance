from google import genai
from google.genai import types

from app.config import settings


class EmbeddingService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.llm_api_key)
        self.model = settings.embedding_model

    def embed_text(self, text: str) -> list[float]:
        response = self.client.models.embed_content(
            model=self.model,
            contents=text,
            config=types.EmbedContentConfig(
                output_dimensionality=768,
            ),
        )

        return response.embeddings[0].values

    def embed_image(self, image_path: str) -> list[float]:
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()

        response = self.client.models.embed_content(
            model=self.model,
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/jpeg",
                )
            ],
            config=types.EmbedContentConfig(
                output_dimensionality=768,
            ),
        )

        return response.embeddings[0].values