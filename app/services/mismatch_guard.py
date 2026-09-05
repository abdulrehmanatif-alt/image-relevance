from dataclasses import dataclass


@dataclass
class GuardResult:
    accepted: bool
    reason: str


class MismatchGuard:
    SIMILARITY_THRESHOLD = 0.30
    MIN_CONFIDENCE = 0.80

    def check(
        self,
        similarity: float,
        image_subject: str,
        image_category: str,
        image_confidence: float,
        post_text: str,
    ) -> GuardResult:

        if similarity < self.SIMILARITY_THRESHOLD:
            return GuardResult(
                accepted=False,
                reason=(
                    f"Similarity score {similarity:.4f} is below "
                    f"the minimum threshold of "
                    f"{self.SIMILARITY_THRESHOLD:.2f}."
                ),
            )

        if image_confidence < self.MIN_CONFIDENCE:
            return GuardResult(
                accepted=False,
                reason=(
                    f"Image confidence {image_confidence:.2f} is below "
                    f"the minimum confidence of "
                    f"{self.MIN_CONFIDENCE:.2f}."
                ),
            )

        post_text_lower = post_text.lower()

        subject_match = (
            image_subject.strip().lower()
            and image_subject.strip().lower() in post_text_lower
        )

        category_match = (
            image_category.strip().lower()
            and image_category.strip().lower() in post_text_lower
        )

        if not subject_match and not category_match:
            return GuardResult(
                accepted=False,
                reason=(
                    f"Post text does not mention the image subject "
                    f"'{image_subject}' or category "
                    f"'{image_category}'."
                ),
            )

        return GuardResult(
            accepted=True,
            reason="Candidate passed similarity, confidence, and metadata checks.",
        )