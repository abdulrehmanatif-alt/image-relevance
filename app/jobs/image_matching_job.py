from app.services.image_matching_service import ImageMatchingService


service = ImageMatchingService()


def run_image_matching(image_url: str, blog_content: str) -> dict:
    return service.analyze(
        image_url=image_url,
        blog_content=blog_content,
    )