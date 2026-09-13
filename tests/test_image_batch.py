from app.jobs.image_batch import find_existing, save_image_to_db
from app.database import SessionLocal
from app.models import Image


def test_find_existing_returns_processed_image():
    dataset = {
        "images": [
            {
                "filename": "fox_001.jpg",
                "status": "processed",
            }
        ]
    }

    result = find_existing(dataset, "fox_001.jpg")

    assert result is not None
    assert result["status"] == "processed"


def test_find_existing_returns_none_for_new_image():
    dataset = {
        "images": [
            {
                "filename": "fox_001.jpg",
                "status": "processed",
            }
        ]
    }

    result = find_existing(dataset, "wolf_001.jpg")

    assert result is None


def test_save_image_to_db_creates_image():
    filename = "db_test_image.jpg"

    try:
        save_image_to_db(
            {
                "filename": filename,
                "status": "processed",
                "subject": "test subject",
                "category": "animal",
                "attributes": ["test"],
                "caption": "test caption",
                "confidence": 0.95,
            }
        )

        with SessionLocal() as db:
            image = db.query(Image).filter(
                Image.filename == filename
            ).first()

            assert image is not None
            assert image.status == "processed"
            assert image.subject == "test subject"
            assert image.confidence == 0.95

    finally:
        with SessionLocal() as db:
            image = db.query(Image).filter(
                Image.filename == filename
            ).first()

            if image:
                db.delete(image)
                db.commit()