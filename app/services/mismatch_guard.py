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
        image_subject: str | None,
        image_category: str | None,
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

        subject = (image_subject or "").strip()
        category = (image_category or "").strip()

        # If vision metadata exists, enforce its confidence and
        # use the most specific available metadata for the mismatch check.
        if subject or category:

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
                subject.lower() in post_text_lower
                if subject
                else False
            )

            category_match = (
                category.lower() in post_text_lower
                if category
                else False
            )

            if subject:
                if not subject_match:
                    return GuardResult(
                        accepted=False,
                        reason=(
                            f"Post text does not mention the image subject "
                            f"'{subject}'."
                        ),
                    )
            elif not category_match:
                return GuardResult(
                    accepted=False,
                    reason=(
                        f"Post text does not mention the image category "
                        f"'{category}'."
                    ),
                )

        return GuardResult(
            accepted=True,
            reason="Candidate passed similarity and available metadata checks.",
        )