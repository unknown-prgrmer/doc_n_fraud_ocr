"""Tests for adapter implementations."""

from datetime import datetime, timezone

import httpx
import pytest

from app.entities.prediction import Prediction, PredictionMetadata
from app.infra.repositories.inmemory.im_image_repository import (
    InMemoryImageRepository,
)
from app.infra.repositories.inmemory.im_metadata_repository import (
    InMemoryMetadataRepository,
)
from app.infra.services.http.image_downloader_service import (
    HttpImageDownloaderService,
)
from app.infra.services.inmemory.stub_ocr_service import StubOCRService


class TestStubOCRService:
    """Test cases for StubOCRService adapter."""

    def test_predict_returns_valid_prediction(self) -> None:
        """Test that OCR service returns a valid prediction."""
        service = StubOCRService()
        image_data = b"fake_image_data"

        result = service.predict(image_data)

        assert isinstance(result, Prediction)
        assert isinstance(result.predicted_text, str)
        assert len(result.predicted_text) > 0
        assert 0.0 <= result.confidence_score <= 1.0

    def test_predict_with_empty_image_raises_error(self) -> None:
        """Test that empty image data raises error."""
        service = StubOCRService()

        with pytest.raises(ValueError, match="Image data cannot be empty"):
            service.predict(b"")

    def test_predict_with_none_raises_error(self) -> None:
        """Test that None image data raises error."""
        service = StubOCRService()

        with pytest.raises((ValueError, TypeError)):
            service.predict(None)  # type: ignore


class TestInMemoryImageRepository:
    """Test cases for InMemoryImageRepository adapter."""

    def test_store_returns_path(self) -> None:
        """Test that store returns a valid path."""
        repo = InMemoryImageRepository()
        image_data = b"fake_image_data"

        path = repo.store(image_data)

        assert isinstance(path, str)
        assert len(path) > 0

    def test_store_retrieves_stored_image(self) -> None:
        """Test that stored image can be retrieved."""
        repo = InMemoryImageRepository()
        image_data = b"fake_image_data"

        path = repo.store(image_data)
        retrieved = repo.retrieve(path)

        assert retrieved == image_data

    def test_retrieve_nonexistent_image_raises_error(self) -> None:
        """Test that retrieving nonexistent image raises error."""
        repo = InMemoryImageRepository()

        with pytest.raises(KeyError):
            repo.retrieve("nonexistent_path")

    def test_store_multiple_images(self) -> None:
        """Test storing multiple images returns different paths."""
        repo = InMemoryImageRepository()
        image_data1 = b"fake_image_data_1"
        image_data2 = b"fake_image_data_2"

        path1 = repo.store(image_data1)
        path2 = repo.store(image_data2)

        assert path1 != path2
        assert repo.retrieve(path1) == image_data1
        assert repo.retrieve(path2) == image_data2


class TestInMemoryMetadataRepository:
    """Test cases for InMemoryMetadataRepository adapter."""

    def test_save_persists_metadata(self) -> None:
        """Test that metadata is persisted."""
        repo = InMemoryMetadataRepository()
        now = datetime.now(timezone.utc)
        prediction = Prediction(predicted_text="Test", confidence_score=0.9)
        metadata = PredictionMetadata(
            timestamp=now,
            source_url="https://example.com/image.jpg",
            image_path="s3://bucket/image.jpg",
        )

        repo.save(metadata, prediction)

        # Verify by retrieving
        records = repo.get_all()
        assert len(records) == 1
        assert records[0].metadata == metadata
        assert records[0].prediction == prediction

    def test_save_multiple_records(self) -> None:
        """Test saving multiple records."""
        repo = InMemoryMetadataRepository()
        now = datetime.now(timezone.utc)

        pred1 = Prediction(predicted_text="Test1", confidence_score=0.9)
        meta1 = PredictionMetadata(
            timestamp=now,
            source_url="https://example.com/image1.jpg",
            image_path="s3://bucket/image1.jpg",
        )

        pred2 = Prediction(predicted_text="Test2", confidence_score=0.8)
        meta2 = PredictionMetadata(
            timestamp=now,
            source_url="https://example.com/image2.jpg",
            image_path="s3://bucket/image2.jpg",
        )

        repo.save(meta1, pred1)
        repo.save(meta2, pred2)

        records = repo.get_all()
        assert len(records) == 2

    def test_get_all_returns_empty_initially(self) -> None:
        """Test that get_all returns empty list initially."""
        repo = InMemoryMetadataRepository()

        records = repo.get_all()

        assert isinstance(records, list)
        assert len(records) == 0

    def test_get_by_source_url(self) -> None:
        """Test retrieving records by source URL."""
        repo = InMemoryMetadataRepository()
        now = datetime.now(timezone.utc)

        pred = Prediction(predicted_text="Test", confidence_score=0.9)
        source_url = "https://example.com/image.jpg"
        meta = PredictionMetadata(
            timestamp=now,
            source_url=source_url,
            image_path="s3://bucket/image.jpg",
        )

        repo.save(meta, pred)

        records = repo.get_by_source_url(source_url)
        assert len(records) == 1
        assert records[0].metadata.source_url == source_url

    def test_get_by_source_url_returns_empty_for_unknown(self) -> None:
        """Test that get_by_source_url returns empty for unknown URL."""
        repo = InMemoryMetadataRepository()

        records = repo.get_by_source_url("https://unknown.com/image.jpg")

        assert len(records) == 0


class TestHttpImageDownloaderService:
    """Test cases for HttpImageDownloaderService adapter."""

    def test_download_success(self) -> None:
        """Return bytes when upstream returns HTTP 200."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(status_code=200, content=b"img")

        client = httpx.Client(transport=httpx.MockTransport(handler))
        service = HttpImageDownloaderService(http_client=client)
        try:
            assert service.download("https://example.com/image.jpg") == b"img"
        finally:
            client.close()

    def test_download_invalid_url_raises_value_error(self) -> None:
        """Raise ValueError when URL format is invalid."""
        service = HttpImageDownloaderService()

        with pytest.raises(ValueError, match="Invalid URL"):
            service.download("not-a-valid-url")

    def test_download_http_error_raises_io_error(self) -> None:
        """Raise IOError when upstream returns non-success status."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(status_code=500, content=b"boom")

        client = httpx.Client(transport=httpx.MockTransport(handler))
        service = HttpImageDownloaderService(http_client=client)
        try:
            with pytest.raises(IOError, match="Download failed"):
                service.download("https://example.com/image.jpg")
        finally:
            client.close()
