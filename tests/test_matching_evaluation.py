import json

from app.services.matching_service import MatchingService
from app.services.similarity_service import cosine_similarity


def test_top_1_precision():
    with open("data/eval_dataset.json", "r", encoding="utf-8") as file:
        dataset = json.load(file)

    service = MatchingService()

    correct = 0
    total = len(dataset["evaluations"])

    for evaluation in dataset["evaluations"]:
        results = service.rank_images(evaluation["post"])

        accepted_results = [
            result for result in results
            if result["accepted"]
        ]

        expected_category = evaluation["expected_category"]

        if not accepted_results:
            print(
                f"\nExpected: {expected_category}"
                f"\nPredicted: NONE"
                f"\nScore: 0.0000"
                f"\nResult: WRONG"
            )
            continue

        top_result = accepted_results[0]
        predicted_filename = top_result["filename"]
        predicted_category = predicted_filename.rsplit("_", 1)[0]

        is_correct = predicted_category == expected_category

        if is_correct:
            correct += 1

        print(
            f"\nExpected: {expected_category}"
            f"\nPredicted: {predicted_filename}"
            f"\nScore: {top_result['score']:.4f}"
            f"\nResult: {'CORRECT' if is_correct else 'WRONG'}"
        )

    precision = correct / total

    print(f"\nTop-1 precision: {precision:.2%}")
    print(f"Correct: {correct}/{total}")

    assert precision == 1.0

def test_forced_mismatch_is_rejected():
    with open("data/dataset.json", "r", encoding="utf-8") as file:
        dataset = json.load(file)

    service = MatchingService()

    # A fox post should not accept a wolf image.
    post_text = "A wild fox walking through a forest."

    wolf_image = next(
        image
        for image in dataset["images"]
        if image["filename"] == "wolf_001.jpg"
    )

    # Get the embedding for the post.
    post_embedding = service.post_embedding_service.embed_post(post_text)

    # Find the forced wolf image embedding.
    image_embedding = next(
        image
        for image in service.image_embeddings
        if image["filename"] == "wolf_001.jpg"
    )

    score = service.mismatch_guard.check(
        similarity=cosine_similarity(
        post_embedding,
        image_embedding["embedding"],
        ),
        image_subject=wolf_image.get("subject", ""),
        image_category=wolf_image.get("category", ""),
        image_confidence=wolf_image.get("confidence", 0.0),
        post_text=post_text,
    )

    print(f"\nForced wolf score: {score}")
    assert score.accepted is False