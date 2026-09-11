import json
from pathlib import Path

from app.services.matching_service import MatchingService


EVAL_DATASET_FILE = Path("data/eval_dataset.json")


class EvaluationService:
    def __init__(self):
        self.matching_service = MatchingService()

        with open(EVAL_DATASET_FILE, "r", encoding="utf-8") as file:
            self.dataset = json.load(file)

    def evaluate(self) -> dict:
        evaluations = self.dataset["evaluations"]

        correct = 0
        results = []

        for evaluation in evaluations:
            post = evaluation["post"]
            expected_category = evaluation["expected_category"]

            ranked_results = self.matching_service.rank_images(post)

            accepted_results = [
                result
                for result in ranked_results
                if result["accepted"]
            ]

            if not accepted_results:
                results.append(
                    {
                        "post": post,
                        "expected_category": expected_category,
                        "predicted_category": None,
                        "filename": "",
                        "score": 0.0,
                        "correct": False,
                    }
                )
                continue

            top_result = accepted_results[0]
            filename = top_result["filename"]

            predicted_category = filename.rsplit("_", 1)[0]

            is_correct = predicted_category == expected_category

            if is_correct:
                correct += 1

            results.append(
                {
                    "post": post,
                    "expected_category": expected_category,
                    "predicted_category": predicted_category,
                    "filename": filename,
                    "score": top_result["score"],
                    "correct": is_correct,
                }
            )

        total = len(evaluations)
        precision = correct / total if total else 0.0

        return {
            "total": total,
            "correct": correct,
            "top_1_precision": precision,
            "results": results,
        }