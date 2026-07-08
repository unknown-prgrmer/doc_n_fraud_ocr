"""Tests for the predict usecase."""

from datetime import datetime, timezone

import pytest

from app.entities.prediction import Prediction, PredictionMetadata
from app.ports.ocr_service import ImageRepository, MetadataRepository, OCRService
from app.usecases.predict_usecase import PredictUsecase


class StubOCRServiceSuccess(OCRService):
    """Stub OCR service returning a fixed prediction."""

    def predict(self, image_data: bytes) -> Prediction:
        """Return a fixed prediction for tests."""
        return Prediction(predicted_text="Sample text", confidence_score=0.92)


class StubOCRServiceFailure(OCRService):
    """Stub OCR service failing on predict."""

    def predict(self, image_data: bytes) -> Prediction:
        """Raise an OCR error."""
        raise ValueError("OCR failed")


class FakeImageRepository(ImageRepository):
    """In-memory fake image repository with call tracking."""

    def __init__(self) -> None:
        """Initialize fake repository."""
        self.store_calls = 0
        self.last_data: bytes | None = None

    def store(self, image_data: bytes) -> str:
        """Store image bytes in memory and return a fake path."""
        self.store_calls += 1
        self.last_data = image_data
        return "s3://bucket/abc123.jpg"


class FakeImageRepositoryFailure(ImageRepository):
    """Fake image repository that always fails."""

    def store(self, image_data: bytes) -> str:
        """Raise a storage error."""
        raise IOError("Storage failed")


class FakeMetadataRepository(MetadataRepository):
    """In-memory fake metadata repository with call tracking."""

    def __init__(self) -> None:
        """Initialize fake metadata repository."""
        self.save_calls = 0
        self.saved: list[tuple[PredictionMetadata, Prediction]] = []

    def save(self, metadata: PredictionMetadata, prediction: Prediction) -> None:
        """Persist a prediction record in memory."""
        self.save_calls += 1
        self.saved.append((metadata, prediction))


class FakeMetadataRepositoryFailure(MetadataRepository):
    """Fake metadata repository that always fails."""

    def save(self, metadata: PredictionMetadata, prediction: Prediction) -> None:
        """Raise a persistence error."""
        raise RuntimeError("DB failed")


class TestPredictUsecase:
    """Test cases for PredictUsecase."""

    def test_predict_with_image_data_success(self) -> None:
        """Persist prediction and metadata on success."""
        image_data = b"fake_image_data"
        source_url = "https://example.com/image.jpg"
        ocr_service = StubOCRServiceSuccess()
        image_repository = FakeImageRepository()
        metadata_repository = FakeMetadataRepository()
        usecase = PredictUsecase(
            ocr_service=ocr_service,
            image_repository=image_repository,
            metadata_repository=metadata_repository,
        )

        result = usecase.predict_from_image_data(image_data, source_url)

        assert result.prediction.predicted_text == "Sample text"
        assert result.metadata.source_url == source_url
        assert result.metadata.image_path == "s3://bucket/abc123.jpg"
        assert image_repository.store_calls == 1
        assert metadata_repository.save_calls == 1

    def test_predict_ocr_service_failure(self) -> None:
        """Stop flow if OCR fails before storage."""
        image_data = b"fake_image_data"
        source_url = "https://example.com/image.jpg"
        ocr_service = StubOCRServiceFailure()
        image_repository = FakeImageRepository()
        metadata_repository = FakeMetadataRepository()
        usecase = PredictUsecase(
            ocr_service=ocr_service,
            image_repository=image_repository,
            metadata_repository=metadata_repository,
        )

        with pytest.raises(ValueError, match="OCR failed"):
            usecase.predict_from_image_data(image_data, source_url)

        assert image_repository.store_calls == 0
        assert metadata_repository.save_calls == 0

    def test_predict_image_storage_failure(self) -> None:
        """Avoid metadata save if image storage fails."""
        usecase = PredictUsecase(
            ocr_service=StubOCRServiceSuccess(),
            image_repository=FakeImageRepositoryFailure(),
            metadata_repository=FakeMetadataRepository(),
        )

        with pytest.raises(IOError, match="Storage failed"):
            usecase.predict_from_image_data(
                b"fake_image_data", "https://example.com/image.jpg"
            )

    def test_predict_metadata_storage_failure(self) -> None:
        """Raise when metadata persistence fails."""
        usecase = PredictUsecase(
            ocr_service=StubOCRServiceSuccess(),
            image_repository=FakeImageRepository(),
            metadata_repository=FakeMetadataRepositoryFailure(),
        )

        with pytest.raises(RuntimeError, match="DB failed"):
            usecase.predict_from_image_data(
                b"fake_image_data", "https://example.com/image.jpg"
            )

    def test_predict_with_annotation(self) -> None:
        """Persist optional annotation."""
        metadata_repository = FakeMetadataRepository()
        usecase = PredictUsecase(
            ocr_service=StubOCRServiceSuccess(),
            image_repository=FakeImageRepository(),
            metadata_repository=metadata_repository,
        )

        result = usecase.predict_from_image_data(
            b"fake_image_data",
            "https://example.com/image.jpg",
            annotation="expected text",
        )

        assert result.metadata.annotation == "expected text"
        assert metadata_repository.saved[0][0].annotation == "expected text"

    def test_predict_timestamp_is_utc(self) -> None:
        """Generate UTC timestamp when persisting record."""
        usecase = PredictUsecase(
            ocr_service=StubOCRServiceSuccess(),
            image_repository=FakeImageRepository(),
            metadata_repository=FakeMetadataRepository(),
        )
        before_call = datetime.now(timezone.utc)

        result = usecase.predict_from_image_data(
            b"fake_image_data", "https://example.com/image.jpg"
        )

        after_call = datetime.now(timezone.utc)
        assert result.metadata.timestamp.tzinfo is not None
        assert before_call <= result.metadata.timestamp <= after_call
