"""Tests for predict endpoint infrastructure."""

import pytest
from fastapi.testclient import TestClient

from app.entities.prediction import Prediction, PredictionMetadata
from app.ports.ocr_service import ImageDownloaderService, MetadataRepository
from app.services.image_service import (
    InMemoryImageRepository,
    InMemoryMetadataRepository,
    StubOCRService,
)
from app.webservice import create_app


class StubImageDownloaderSuccess(ImageDownloaderService):
    """Downloader stub returning deterministic bytes."""

    def download(self, source_url: str) -> bytes:
        """Return fake image bytes for any URL."""
        return b"fake_jpeg_data"


class StubImageDownloaderInvalidUrl(ImageDownloaderService):
    """Downloader stub raising invalid URL errors."""

    def download(self, source_url: str) -> bytes:
        """Raise invalid URL error."""
        raise ValueError("Invalid URL")


class StubImageDownloaderFailure(ImageDownloaderService):
    """Downloader stub raising infrastructure failures."""

    def download(self, source_url: str) -> bytes:
        """Raise download error."""
        raise IOError("Download failed")


class FakeImageRepositoryFailure(InMemoryImageRepository):
    """Image repository fake that raises IOError."""

    def store(self, image_data: bytes) -> str:
        """Raise IOError to simulate infrastructure failure."""
        raise IOError("Image storage failed")


class FakeMetadataRepositoryFailure(MetadataRepository):
    """Metadata repository fake that always fails."""

    def save(self, metadata: PredictionMetadata, prediction: Prediction) -> None:
        """Raise runtime error to simulate database failure."""
        raise RuntimeError("DB failed")


@pytest.fixture(name="ocr_service")
def ocr_service_fixture() -> StubOCRService:
    """Create OCR service."""
    return StubOCRService()


@pytest.fixture(name="image_repository")
def image_repository_fixture() -> InMemoryImageRepository:
    """Create image repository."""
    return InMemoryImageRepository()


@pytest.fixture(name="metadata_repository")
def metadata_repository_fixture() -> InMemoryMetadataRepository:
    """Create metadata repository."""
    return InMemoryMetadataRepository()


def _build_client(
    downloader: ImageDownloaderService,
    image_repository: InMemoryImageRepository,
    metadata_repository: InMemoryMetadataRepository,
) -> TestClient:
    """Create client with injected fake dependencies."""
    app = create_app(
        ocr_service=StubOCRService(),
        image_repository=image_repository,
        metadata_repository=metadata_repository,
        image_downloader_service=downloader,
    )
    return TestClient(app)


class TestPredictEndpoint:
    """Test cases for predict endpoint."""

    def test_predict_with_valid_url_success(
        self,
        image_repository: InMemoryImageRepository,
        metadata_repository: InMemoryMetadataRepository,
    ) -> None:
        """Return prediction and persist metadata on success."""
        client = _build_client(
            StubImageDownloaderSuccess(), image_repository, metadata_repository
        )

        response = client.post(
            "/predict",
            json={"url": "https://example.com/image.jpg"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "predicted_text" in data
        assert "score" in data
        assert 0.0 <= data["score"] <= 1.0

        records = metadata_repository.get_all()
        assert len(records) == 1
        assert records[0].metadata.source_url == "https://example.com/image.jpg"

    def test_predict_endpoint_requires_url(
        self,
        image_repository: InMemoryImageRepository,
        metadata_repository: InMemoryMetadataRepository,
    ) -> None:
        """Reject request without URL."""
        client = _build_client(
            StubImageDownloaderSuccess(), image_repository, metadata_repository
        )

        response = client.post("/predict", json={})

        assert response.status_code == 422

    def test_predict_with_invalid_url_format(
        self,
        image_repository: InMemoryImageRepository,
        metadata_repository: InMemoryMetadataRepository,
    ) -> None:
        """Map invalid URL to HTTP 400."""
        client = _build_client(
            StubImageDownloaderInvalidUrl(), image_repository, metadata_repository
        )

        response = client.post("/predict", json={"url": "not_a_valid_url"})

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid URL"
        assert len(metadata_repository.get_all()) == 0

    def test_predict_with_download_failure(
        self,
        image_repository: InMemoryImageRepository,
        metadata_repository: InMemoryMetadataRepository,
    ) -> None:
        """Map download failure to HTTP 502."""
        client = _build_client(
            StubImageDownloaderFailure(), image_repository, metadata_repository
        )

        response = client.post(
            "/predict",
            json={"url": "https://example.com/image.jpg"},
        )

        assert response.status_code == 502
        assert response.json()["detail"] == "Download failed"
        assert len(metadata_repository.get_all()) == 0

    def test_predict_with_annotation(
        self,
        image_repository: InMemoryImageRepository,
        metadata_repository: InMemoryMetadataRepository,
    ) -> None:
        """Persist annotation when provided."""
        client = _build_client(
            StubImageDownloaderSuccess(), image_repository, metadata_repository
        )

        response = client.post(
            "/predict",
            json={
                "url": "https://example.com/image.jpg",
                "annotation": "Sample annotation",
            },
        )

        assert response.status_code == 200
        records = metadata_repository.get_all()
        assert records[0].metadata.annotation == "Sample annotation"

    def test_predict_timestamp_is_persisted_utc(
        self,
        image_repository: InMemoryImageRepository,
        metadata_repository: InMemoryMetadataRepository,
    ) -> None:
        """Persist UTC timestamp for successful requests."""
        client = _build_client(
            StubImageDownloaderSuccess(), image_repository, metadata_repository
        )

        response = client.post(
            "/predict",
            json={"url": "https://example.com/image.jpg"},
        )

        assert response.status_code == 200
        assert metadata_repository.get_all()[0].metadata.timestamp.tzinfo is not None

    def test_predict_with_metadata_persistence_failure_returns_500(
        self,
        image_repository: InMemoryImageRepository,
    ) -> None:
        """Map metadata persistence failure to HTTP 500."""
        app = create_app(
            ocr_service=StubOCRService(),
            image_repository=image_repository,
            metadata_repository=FakeMetadataRepositoryFailure(),
            image_downloader_service=StubImageDownloaderSuccess(),
        )
        client = TestClient(app)

        response = client.post(
            "/predict",
            json={"url": "https://example.com/image.jpg"},
        )

        assert response.status_code == 500
        assert response.json()["detail"] == "DB failed"

    def test_predict_with_image_storage_failure_returns_502(
        self,
        metadata_repository: InMemoryMetadataRepository,
    ) -> None:
        """Map storage failure in usecase to HTTP 502."""
        app = create_app(
            ocr_service=StubOCRService(),
            image_repository=FakeImageRepositoryFailure(),
            metadata_repository=metadata_repository,
            image_downloader_service=StubImageDownloaderSuccess(),
        )
        client = TestClient(app)

        response = client.post(
            "/predict",
            json={"url": "https://example.com/image.jpg"},
        )

        assert response.status_code == 502
        assert response.json()["detail"] == "Image storage failed"
