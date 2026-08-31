import pytest
from pydantic import ValidationError

from app.schemas.image import ImageUnderstanding


def test_valid_image_understanding():
    result = ImageUnderstanding(
        subject="red fox",
        category="animal",
        attributes=["orange fur", "bushy tail"],
        caption="A red fox standing in a field.",
        confidence=0.96,
    )

    assert result.subject == "red fox"
    assert result.category == "animal"
    assert result.confidence == 0.96
    assert "orange fur" in result.attributes


def test_confidence_cannot_exceed_one():
    with pytest.raises(ValidationError):
        ImageUnderstanding(
            subject="fox",
            category="animal",
            caption="A fox.",
            confidence=1.5,
        )


def test_confidence_cannot_be_negative():
    with pytest.raises(ValidationError):
        ImageUnderstanding(
            subject="fox",
            category="animal",
            caption="A fox.",
            confidence=-0.1,
        )


def test_empty_subject_is_rejected():
    with pytest.raises(ValidationError):
        ImageUnderstanding(
            subject="",
            category="animal",
            caption="A fox.",
            confidence=0.9,
        )