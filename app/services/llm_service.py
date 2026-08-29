from app.config import settings


class LLMService:
    def __init__(self):
        self.provider = settings.llm_provider
        self.model = settings.llm_model
        self.api_key = settings.llm_api_key

    def analyze_image_and_content(
        self,
        image_url: str,
        blog_content: str,
    ) -> dict:
        return {
            "relevance_score": 0.0,
            "explanation": "LLM analysis has not been implemented yet.",
        }