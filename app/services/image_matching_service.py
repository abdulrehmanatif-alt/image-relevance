from app.services.llm_service import LLMService


class ImageMatchingService:
    def __init__(self):
        self.llm_service = LLMService()

    def analyze(self, image_url: str, blog_content: str) -> dict:
        return self.llm_service.analyze_image_and_content(
            image_url=image_url,
            blog_content=blog_content,
        )