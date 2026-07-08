"""Tests for domain entities."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.entities.prediction import (
    Prediction,
    PredictionMetadata,
    PredictionRecord,
)


class TestPrediction:
    """Test cases for Prediction entity."""

    def test_prediction_creation_valid(self) -> None:
        """Test creating a valid prediction."""
        pred = Prediction(predicted_text="Hello", confidence_score=0.95)
        assert pred.predicted_text == "Hello"
        assert pred.confidence_score == 0.95

    def test_prediction_confidence_score_zero(self) -> None:
        """Test prediction with zero confidence score."""
        pred = Prediction(predicted_text="Text", confidence_score=0.0)
        assert pred.confidence_score == 0.0

    def test_prediction_confidence_score_one(self) -> None:
        """Test prediction with maximum confidence score."""
        pred = Prediction(predicted_text="Text", confidence_score=1.0)
        assert pred.confidence_score == 1.0

    def test_prediction_invalid_confidence_score_negative(self) -> None:
        """Test that confidence score below 0.0 raises error."""
        with pytest.raises(ValueError):
            Prediction(predicted_text="Text", confidence_score=-0.1)

    def test_prediction_invalid_confidence_score_above_one(self) -> None:
        """Test that confidence score above 1.0 raises error."""
        with pytest.raises(ValueError):
            Prediction(predicted_text="Text", confidence_score=1.1)

    def test_prediction_empty_text(self) -> None:
        """Test that empty predicted text raises error."""
        with pytest.raises(ValueError):
            Prediction(predicted_text="", confidence_score=0.5)

    def test_prediction_immutable(self) -> None:
        """Test that prediction is immutable."""
        pred = Prediction(predicted_text="Text", confidence_score=0.5)
        with pytest.raises(ValidationError):
            pred.predicted_text = "Modified"  # type: ignore


class TestPredictionMetadata:
    """Test cases for PredictionMetadata entity."""

    def test_metadata_creation_valid(self) -> None:
        """Test creating valid metadata."""
        now = datetime.now(timezone.utc)
        meta = PredictionMetadata(
            timestamp=now,
            source_url="https://example.com/image.jpg",
            image_path="s3://bucket/image.jpg",
            annotation="sample text"
        )
        assert meta.timestamp == now
        assert meta.source_url == "https://example.com/image.jpg"
        assert meta.image_path == "s3://bucket/image.jpg"
        assert meta.annotation == "sample text"

    def test_metadata_optional_annotation(self) -> None:
        """Test metadata without annotation."""
        now = datetime.now(timezone.utc)
        meta = PredictionMetadata(
            timestamp=now,
            source_url="https://example.com/image.jpg",
            image_path="s3://bucket/image.jpg"
        )
        assert meta.annotation is None

    def test_metadata_empty_source_url(self) -> None:
        """Test that empty source URL raises error."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            PredictionMetadata(
                timestamp=now,
                source_url="",
                image_path="s3://bucket/image.jpg"
            )

    def test_metadata_empty_image_path(self) -> None:
        """Test that empty image path raises error."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            PredictionMetadata(
                timestamp=now,
                source_url="https://example.com/image.jpg",
                image_path=""
            )

    def test_metadata_naive_timestamp(self) -> None:
        """Test that naive (non-UTC) timestamp raises error."""
        naive_time = datetime(2026, 1, 1, 12, 0, 0)
        with pytest.raises(ValueError, match="Timestamp must be timezone-aware"):
            PredictionMetadata(
                timestamp=naive_time,
                source_url="https://example.com/image.jpg",
                image_path="s3://bucket/image.jpg"
            )

    def test_metadata_immutable(self) -> None:
        """Test that metadata is immutable."""
        now = datetime.now(timezone.utc)
        meta = PredictionMetadata(
            timestamp=now,
            source_url="https://example.com/image.jpg",
            image_path="s3://bucket/image.jpg"
        )
        with pytest.raises(ValidationError):
            meta.source_url = "modified"  # type: ignore


class TestPredictionRecord:
    """Test cases for PredictionRecord aggregate entity."""

    def test_record_creation(self) -> None:
        """Test creating a prediction record."""
        now = datetime.now(timezone.utc)
        pred = Prediction(predicted_text="Hello", confidence_score=0.95)
        meta = PredictionMetadata(
            timestamp=now,
            source_url="https://example.com/image.jpg",
            image_path="s3://bucket/image.jpg"
        )
        record = PredictionRecord(prediction=pred, metadata=meta)

        assert record.prediction == pred
        assert record.metadata == meta

    def test_record_immutable(self) -> None:
        """Test that prediction record is immutable."""
        now = datetime.now(timezone.utc)
        pred = Prediction(predicted_text="Hello", confidence_score=0.95)
        meta = PredictionMetadata(
            timestamp=now,
            source_url="https://example.com/image.jpg",
            image_path="s3://bucket/image.jpg"
        )
        record = PredictionRecord(prediction=pred, metadata=meta)

        with pytest.raises(ValidationError):
            record.prediction = pred  # type: ignore
