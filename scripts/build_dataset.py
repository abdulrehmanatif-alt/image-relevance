import json
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw


PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGE_DIR = PROJECT_ROOT / "data" / "images"
DATASET_FILE = PROJECT_ROOT / "data" / "dataset.json"

IMAGE_SIZE = (512, 512)
IMAGES_PER_CATEGORY = 5

CATEGORIES = [
    "fox",
    "wolf",
    "cat",
    "dog",
    "bird",
    "horse",
    "motorcycle",
    "car",
    "mountain",
    "plain",
]


def create_background(draw, category):
    draw.rectangle(
        (0, 0, 511, 511),
        fill=(225, 235, 220),
    )

    # Sky
    draw.rectangle(
        (0, 0, 511, 300),
        fill=(150, 205, 235),
    )

    # Ground
    draw.rectangle(
        (0, 300, 511, 511),
        fill=(115, 165, 90),
    )


def draw_animal(draw, category, variation):
    center_x = 256
    center_y = 270

    if category in {"fox", "wolf", "cat", "dog"}:
        body_colors = {
            "fox": (205, 105, 45),
            "wolf": (115, 115, 120),
            "cat": (170, 170, 170),
            "dog": (145, 95, 55),
        }

        color = body_colors[category]

        # Body
        draw.ellipse(
            (
                center_x - 120,
                center_y - 30,
                center_x + 120,
                center_y + 90,
            ),
            fill=color,
        )

        # Head
        draw.ellipse(
            (
                center_x - 75,
                center_y - 120,
                center_x + 75,
                center_y + 20,
            ),
            fill=color,
        )

        # Ears
        draw.polygon(
            [
                (center_x - 60, center_y - 100),
                (center_x - 95, center_y - 170),
                (center_x - 20, center_y - 120),
            ],
            fill=color,
        )

        draw.polygon(
            [
                (center_x + 60, center_y - 100),
                (center_x + 95, center_y - 170),
                (center_x + 20, center_y - 120),
            ],
            fill=color,
        )

        # Eyes
        draw.ellipse(
            (
                center_x - 38,
                center_y - 70,
                center_x - 22,
                center_y - 54,
            ),
            fill=(20, 20, 20),
        )

        draw.ellipse(
            (
                center_x + 22,
                center_y - 70,
                center_x + 38,
                center_y - 54,
            ),
            fill=(20, 20, 20),
        )

        # Nose
        draw.ellipse(
            (
                center_x - 12,
                center_y - 30,
                center_x + 12,
                center_y - 8,
            ),
            fill=(30, 30, 30),
        )

        # Tail
        tail_offset = 30 + variation * 8

        draw.line(
            [
                (center_x + 95, center_y + 30),
                (center_x + 150, center_y - tail_offset),
                (center_x + 195, center_y + 20),
            ],
            fill=color,
            width=35,
        )

    elif category == "bird":
        draw.ellipse(
            (
                center_x - 80,
                center_y - 40,
                center_x + 80,
                center_y + 100,
            ),
            fill=(70, 90, 140),
        )

        draw.ellipse(
            (
                center_x + 35,
                center_y - 95,
                center_x + 125,
                center_y - 5,
            ),
            fill=(70, 90, 140),
        )

        draw.polygon(
            [
                (center_x + 120, center_y - 55),
                (center_x + 175, center_y - 35),
                (center_x + 120, center_y - 20),
            ],
            fill=(220, 175, 60),
        )

        draw.polygon(
            [
                (center_x - 20, center_y),
                (center_x - 125, center_y - 60),
                (center_x - 70, center_y + 60),
            ],
            fill=(50, 70, 120),
        )

    elif category == "horse":
        color = (120, 75, 45)

        draw.ellipse(
            (
                center_x - 125,
                center_y - 20,
                center_x + 120,
                center_y + 100,
            ),
            fill=color,
        )

        draw.rectangle(
            (
                center_x + 75,
                center_y - 90,
                center_x + 125,
                center_y + 40,
            ),
            fill=color,
        )

        draw.ellipse(
            (
                center_x + 60,
                center_y - 125,
                center_x + 145,
                center_y - 40,
            ),
            fill=color,
        )

        for leg_x in [-75, -20, 45, 90]:
            draw.rectangle(
                (
                    center_x + leg_x,
                    center_y + 60,
                    center_x + leg_x + 25,
                    center_y + 180,
                ),
                fill=color,
            )

        draw.line(
            [
                (center_x - 120, center_y + 15),
                (center_x - 170, center_y - 40),
            ],
            fill=(70, 45, 30),
            width=30,
        )


def draw_vehicle(draw, category, variation):
    center_x = 256
    center_y = 330

    if category == "car":
        body_color = (190, 45 + variation * 10, 45)

        draw.rounded_rectangle(
            (
                center_x - 170,
                center_y - 55,
                center_x + 170,
                center_y + 65,
            ),
            radius=30,
            fill=body_color,
        )

        draw.polygon(
            [
                (center_x - 100, center_y - 55),
                (center_x - 45, center_y - 130),
                (center_x + 70, center_y - 130),
                (center_x + 120, center_y - 55),
            ],
            fill=body_color,
        )

        for wheel_x in [-105, 105]:
            draw.ellipse(
                (
                    center_x + wheel_x - 35,
                    center_y + 35,
                    center_x + wheel_x + 35,
                    center_y + 105,
                ),
                fill=(30, 30, 30),
            )

    elif category == "motorcycle":
        draw.line(
            [
                (center_x - 120, center_y + 50),
                (center_x, center_y - 30),
                (center_x + 120, center_y + 50),
            ],
            fill=(45, 45, 45),
            width=20,
        )

        for wheel_x in [-120, 120]:
            draw.ellipse(
                (
                    center_x + wheel_x - 45,
                    center_y + 5,
                    center_x + wheel_x + 45,
                    center_y + 95,
                ),
                outline=(30, 30, 30),
                width=15,
            )

        draw.ellipse(
            (
                center_x - 30,
                center_y - 100,
                center_x + 30,
                center_y - 40,
            ),
            fill=(50, 50, 50),
        )


def draw_landscape(draw, category, variation):
    if category == "mountain":
        draw.polygon(
            [
                (0, 360),
                (100, 230 - variation * 5),
                (180, 330),
                (300, 150 + variation * 5),
                (430, 330),
                (512, 220),
                (512, 512),
                (0, 512),
            ],
            fill=(80, 100, 90),
        )

        # Snow peaks
        draw.polygon(
            [
                (300, 150 + variation * 5),
                (270, 205),
                (300, 190),
                (325, 205),
            ],
            fill=(240, 240, 240),
        )

    elif category == "plain":
        draw.rectangle(
            (0, 260, 511, 511),
            fill=(150, 190, 80),
        )

        for x in range(20, 500, 35):
            height = 30 + ((x + variation * 17) % 50)

            draw.line(
                [
                    (x, 450),
                    (x + 5, 450 - height),
                ],
                fill=(80, 130, 50),
                width=5,
            )


def add_label(draw, category, variation):
    # Small label intentionally makes the synthetic fixture
    # easy to inspect during development.
    draw.rectangle(
        (15, 15, 190, 55),
        fill=(255, 255, 255),
    )

    draw.text(
        (25, 25),
        f"{category} #{variation}",
        fill=(20, 20, 20),
    )


def create_image(category, variation):
    image = Image.new(
        "RGB",
        IMAGE_SIZE,
        (255, 255, 255),
    )

    draw = ImageDraw.Draw(image)

    create_background(
        draw,
        category,
    )

    if category in {
        "fox",
        "wolf",
        "cat",
        "dog",
        "bird",
        "horse",
    }:
        draw_animal(
            draw,
            category,
            variation,
        )

    elif category in {
        "car",
        "motorcycle",
    }:
        draw_vehicle(
            draw,
            category,
            variation,
        )

    elif category in {
        "mountain",
        "plain",
    }:
        draw_landscape(
            draw,
            category,
            variation,
        )

    add_label(
        draw,
        category,
        variation,
    )

    # Slight deterministic variation.
    angle = [-3, -1, 0, 1, 3][variation - 1]

    image = image.rotate(
        angle,
        expand=False,
        fillcolor=(225, 235, 220),
    )

    return image


def main():
    IMAGE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    records = []

    for category in CATEGORIES:
        for variation in range(
            1,
            IMAGES_PER_CATEGORY + 1,
        ):
            image_id = (
                f"{category}_{variation:03d}"
            )

            filename = f"{image_id}.jpg"

            path = IMAGE_DIR / filename

            image = create_image(
                category,
                variation,
            )

            image.save(
                path,
                format="JPEG",
                quality=92,
            )

            records.append(
                {
                    "id": image_id,
                    "category": category,
                    "filename": filename,
                    "path": f"data/images/{filename}",
                    "source": "synthetic-development",
                    "license": "Project-generated",
                    "resolution": "512x512",
                }
            )

    dataset = {
        "version": "dev-1.0",
        "purpose": (
            "Development fixture for the image "
            "understanding and matching pipeline."
        ),
        "final_dataset": False,
        "target_image_count": 50,
        "images": records,
        "category_counts": {
            category: IMAGES_PER_CATEGORY
            for category in CATEGORIES
        },
    }

    DATASET_FILE.write_text(
        json.dumps(
            dataset,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("=" * 60)
    print("Development dataset created")
    print("=" * 60)
    print(f"Images: {len(records)}")
    print(f"Manifest: {DATASET_FILE}")
    print()

    for category in CATEGORIES:
        print(
            f"  {category}: "
            f"{IMAGES_PER_CATEGORY}"
        )


if __name__ == "__main__":
    main()
    