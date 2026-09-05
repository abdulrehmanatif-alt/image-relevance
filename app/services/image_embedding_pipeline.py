import json
from pathlib import Path

from app.services.embedding_service import EmbeddingService


IMAGES_DIR = Path("data/images")
OUTPUT_FILE = Path("data/image_embeddings.json")


def build_image_embeddings():
    service = EmbeddingService()

    embeddings = []

    image_files = sorted(IMAGES_DIR.glob("*.jpg"))

    print(f"Found {len(image_files)} images.")

    for index, image_path in enumerate(image_files, start=1):
        print(f"[{index}/{len(image_files)}] Embedding {image_path.name}...")

        embedding = service.embed_image(str(image_path))

        embeddings.append(
            {
                "filename": image_path.name,
                "path": str(image_path),
                "embedding": embedding,
            }
        )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(embeddings, file)

    print()
    print(f"Saved {len(embeddings)} image embeddings to {OUTPUT_FILE}")


if __name__ == "__main__":
    build_image_embeddings()