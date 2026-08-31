from app.jobs.image_batch import find_existing


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