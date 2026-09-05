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

        return GuardResult(
            accepted=True,
            reason="Candidate passed similarity and confidence checks.",
        )