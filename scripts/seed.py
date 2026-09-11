import json
from pathlib import Path


DATASET_FILE = Path("data/dataset.json")
EMBEDDINGS_FILE = Path("data/image_embeddings.json")


def seed():
    if not DATASET_FILE.exists():
        raise FileNotFoundError(f"Missing dataset: {DATASET_FILE}")

    if not EMBEDDINGS_FILE.exists():
        raise FileNotFoundError(
            f"Missing embeddings: {EMBEDDINGS_FILE}. "
            "Generate them before running the seed step."
        )

    with open(DATASET_FILE, "r", encoding="utf-8") as file:
        dataset = json.load(file)

    with open(EMBEDDINGS_FILE, "r", encoding="utf-8") as file:
        embeddings = json.load(file)

    print(f"Dataset contains {len(dataset['images'])} images.")
    print(f"Embeddings contain {len(embeddings)} images.")
    print("Local seed data is ready.")


if __name__ == "__main__":
    seed()