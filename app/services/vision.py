import json
from pathlib import Path

from google import genai
from google.genai import types

from app.config import settings
from app.schemas.image import ImageUnderstanding
from app.services.ai_cost_service import AICostService


class VisionService:
    def __init__(self):
        if not settings.llm_api_key:
            raise ValueError("LLM_API_KEY is not configured.")

        self.client = genai.Client(
            api_key=settings.llm_api_key
        )
        self.cost_service = AICostService()

    def understand_image(
        self,
        image_path: str,
    ) -> tuple[ImageUnderstanding, dict]:
        path = Path(image_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Image not found: {image_path}"
            )

        image_bytes = path.read_bytes()

        prompt = """
Analyze this image for an image-to-blog-post matching system.

Return ONLY valid JSON matching this exact structure:

{
  "subject": "specific main subject",
  "category": "broad category",
  "attributes": ["attribute 1", "attribute 2"],
  "caption": "short factual description of the image",
  "confidence": 0.0
}

Rules:
- subject must identify the main visible subject.
- category must be exactly one of: animal, vehicle, landscape, object, person, illustration.
- For an illustration or digital artwork depicting an animal, use category "animal" rather than "illustration".
- subject should identify the actual depicted subject, such as "red fox", "gray wolf", "cat", or "horse".
- attributes should contain useful visible characteristics.
- caption must describe only what is visibly present.
- confidence must be a number from 0.0 to 1.0.
- Do not include markdown.
- Do not include additional fields.
"""

        if not self.cost_service.check_budget(
            settings.ai_call_budget_estimate
        ):
            raise RuntimeError(
                "AI budget limit exceeded."
            )

        response = self.client.models.generate_content(
            model=settings.llm_model,
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/jpeg",
                ),
                prompt,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ImageUnderstanding,
            ),
        )

        data = json.loads(response.text)

        result = ImageUnderstanding.model_validate(data)

        usage = response.usage_metadata

        input_tokens = (
            usage.prompt_token_count
            if usage
            else None
        )

        output_tokens = (
            usage.candidates_token_count
            if usage
            else None
        )

        estimated_cost = self.cost_service.estimate_cost(
            input_tokens,
            output_tokens,
        )

        self.cost_service.record_call(
            operation="vision",
            provider="gemini",
            model=settings.llm_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=estimated_cost,
            success=True,
        )

        usage_data = {
            "prompt_tokens": (
                input_tokens
                if input_tokens is not None
                else 0
            ),
            "output_tokens": (
                output_tokens
                if output_tokens is not None
                else 0
            ),
            "thoughts_tokens": (
                usage.thoughts_token_count
                if usage
                else 0
            ),
            "total_tokens": (
                usage.total_token_count
                if usage
                else 0
            ),
            "estimated_cost": estimated_cost,
        }

        return result, usage_data