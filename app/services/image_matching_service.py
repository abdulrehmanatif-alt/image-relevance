from app.services.matching_service import MatchingService


class ImageMatchingService:
    def __init__(self):
        self.matching_service = MatchingService()

    def analyze(self, blog_content: str) -> dict:
        results = self.matching_service.rank_images(blog_content)

        accepted_results = [
            result for result in results
            if result["accepted"]
        ]

        if not accepted_results:
            return {
                "filename": "",
                "score": 0.0,
                "accepted": False,
                "explanation": (
                    "No image passed the mismatch guard for this blog post."
                ),
            }

        best_match = accepted_results[0]

        return {
            "filename": best_match["filename"],
            "score": best_match["score"],
            "accepted": True,
            "explanation": best_match["reason"],
        }