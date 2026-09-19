from pathlib import Path

from app.database import SessionLocal
from app.models import Image
from app.services.embedding_service import EmbeddingService


IMAGES_DIR = Path("data/images")


def build_image_embeddings():
    service = EmbeddingService()
    db = SessionLocal()

    image_files = sorted(IMAGES_DIR.glob("*.jpg"))

    print(f"Found {len(image_files)} images.")

    try:
        for index, image_path in enumerate(image_files, start=1):
            print(f"[{index}/{len(image_files)}] Embedding {image_path.name}...")

            image_record = (
                db.query(Image)
                .filter(Image.filename == image_path.name)
                .first()
            )

            if image_record is None:
                print(f"  Skipping {image_path.name}: database record not found.")
                continue

            embedding = service.embed_image(str(image_path))

            image_record.embedding = embedding
            db.commit()

            print(f"  Saved embedding to PostgreSQL.")

    finally:
        db.close()

    print()
    print("Image embedding pipeline completed.")


if __name__ == "__main__":
    build_image_embeddings()