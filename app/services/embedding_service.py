from google import genai
from google.genai import types

from app.config import settings
from app.services.ai_cost_service import AICostService


class EmbeddingService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.llm_api_key)
        self.model = settings.embedding_model
        self.cost_service = AICostService()

    def embed_text(self, text: str) -> list[float]:
        if not self.cost_service.check_budget(
            settings.ai_call_budget_estimate
        ):
            raise RuntimeError(
                "AI budget limit exceeded."
            )
        response = self.client.models.embed_content(
            model=self.model,
            contents=text,
            config=types.EmbedContentConfig(
                output_dimensionality=768,
            ),
        )

        self.cost_service.record_call(
            operation="text_embedding",
            provider="gemini",
            model=self.model,
            input_tokens=None,
            output_tokens=None,
            estimated_cost=0.0,
            success=True,
        )

        return response.embeddings[0].values

    def embed_image(self, image_path: str) -> list[float]:
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()

        if not self.cost_service.check_budget(
            settings.ai_call_budget_estimate
        ):
            raise RuntimeError(
                "AI budget limit exceeded."
            )

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

        self.cost_service.record_call(
            operation="image_embedding",
            provider="gemini",
            model=self.model,
            input_tokens=None,
            output_tokens=None,
            estimated_cost=0.0,
            success=True,
        )

        return response.embeddings[0].values