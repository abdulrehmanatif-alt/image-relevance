import json
from pathlib import Path

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Image


DATASET_FILE = Path("data/dataset.json")
EMBEDDINGS_FILE = Path("data/image_embeddings.json")


def seed():
    with open(DATASET_FILE, "r", encoding="utf-8") as file:
        dataset = json.load(file)

    with open(EMBEDDINGS_FILE, "r", encoding="utf-8") as file:
        embeddings = json.load(file)

    embedding_map = {
        item["filename"]: item["embedding"]
        for item in embeddings
    }

    with SessionLocal() as db:
        for record in dataset["images"]:
            filename = record["filename"]

            existing = db.scalar(
                select(Image).where(Image.filename == filename)
            )

            if existing:
                continue

            db.add(
                Image(
                    filename=filename,
                    status=record.get("status", "pending"),
                    subject=record.get("subject"),
                    category=record.get("category"),
                    attributes=record.get("attributes"),
                    caption=record.get("caption"),
                    confidence=record.get("confidence"),
                    embedding=embedding_map.get(filename),
                    error=record.get("error"),
                )
            )

        db.commit()

        count = db.query(Image).count()
        print(f"Database contains {count} images.")


if __name__ == "__main__":
    seed()