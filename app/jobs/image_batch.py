import json
import time
from pathlib import Path

from app.services.vision import VisionService


DATASET_PATH = Path("data/dataset.json")
IMAGE_DIR = Path("data/images")

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2


def load_dataset() -> dict:
    if DATASET_PATH.exists():
        with DATASET_PATH.open("r", encoding="utf-8") as file:
            return json.load(file)

    return {
        "images": [],
        "category_counts": {},
        "final_dataset": False,
    }


def save_dataset(dataset: dict) -> None:
    DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)

    with DATASET_PATH.open("w", encoding="utf-8") as file:
        json.dump(dataset, file, indent=2, ensure_ascii=False)


def find_existing(dataset: dict, filename: str) -> dict | None:
    for item in dataset["images"]:
        if item.get("filename") == filename:
            return item

    return None


def process_image(
    service: VisionService,
    image_path: Path,
) -> tuple[dict | None, int, str | None]:
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result, usage = service.understand_image(str(image_path))

            return (
               {
                    "filename": image_path.name,
                    "path": str(image_path).replace("\\", "/"),
                    "subject": result.subject,
                    "category": result.category.value,
                    "attributes": result.attributes,
                    "caption": result.caption,
                    "confidence": result.confidence,
                    "status": "processed",
                    "attempts": attempt,
                    "usage": usage,
                },
                attempt,
                None,
            )

        except Exception as exc:
            last_error = str(exc)

            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)

    return None, MAX_RETRIES, last_error


def run_batch() -> None:
    dataset = load_dataset()
    service = VisionService()

    image_paths = sorted(IMAGE_DIR.glob("*.jpg"))

    print(f"Found {len(image_paths)} images.")

    processed = 0
    skipped = 0
    failed = 0

    for image_path in image_paths:
        existing = find_existing(dataset, image_path.name)

        if existing and existing.get("status") == "processed":
            print(f"Skipping already processed: {image_path.name}")
            skipped += 1
            continue

        print(f"Processing: {image_path.name}")

        result, attempts, error = process_image(
            service,
            image_path,
        )

        if result is not None:
            if existing:
                dataset["images"].remove(existing)

            dataset["images"].append(result)

            print(
                f"  OK: {result['subject']} "
                f"(confidence={result['confidence']})"
            )

            processed += 1

        else:
            failure = {
                "filename": image_path.name,
                "path": str(image_path).replace("\\", "/"),
                "status": "failed",
                "attempts": attempts,
                "error": error,
            }

            if existing:
                dataset["images"].remove(existing)

            dataset["images"].append(failure)

            print(f"  FAILED: {error}")

            failed += 1

        save_dataset(dataset)

    category_counts = {}

    for item in dataset["images"]:
        category = item.get("category")

        if category:
            category_counts[category] = (
                category_counts.get(category, 0) + 1
            )

    dataset["category_counts"] = category_counts
    total_prompt_tokens = sum(
        item.get("usage", {}).get("prompt_tokens", 0)
        for item in dataset["images"]
    )

    total_output_tokens = sum(
        item.get("usage", {}).get("output_tokens", 0)
        for item in dataset["images"]
    )

    total_thoughts_tokens = sum(
        item.get("usage", {}).get("thoughts_tokens", 0)
        for item in dataset["images"]
    )

    total_tokens = sum(
        item.get("usage", {}).get("total_tokens", 0)
        for item in dataset["images"]
    )

    estimated_cost = sum(
        item.get("usage", {}).get("estimated_cost", 0.0)
        for item in dataset["images"]
    )

    dataset["usage_summary"] = {
        "prompt_tokens": total_prompt_tokens,
        "output_tokens": total_output_tokens,
        "thoughts_tokens": total_thoughts_tokens,
        "total_tokens": total_tokens,
        "estimated_cost": estimated_cost,
    }

    successful = sum(
        1
        for item in dataset["images"]
        if item.get("status") == "processed"
    )

    dataset["final_dataset"] = (
        len(image_paths) == 50
        and successful == 50
        and failed == 0
    )

    save_dataset(dataset)

    print()
    print("Batch complete.")
    print(f"Processed this run: {processed}")
    print(f"Skipped: {skipped}")
    print(f"Failed: {failed}")
    print(f"Successful total: {successful}")
    print(f"Final dataset: {dataset['final_dataset']}")


if __name__ == "__main__":
    run_batch()