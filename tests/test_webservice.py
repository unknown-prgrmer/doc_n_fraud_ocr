"""Implement tests for webservice functions. Tests files are not documented by choice."""

import json

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.infra.fastapi.exceptions.exceptions import BaseAPIException
from app.infra.repositories.minio.minio_image_repository import (
    MinioImageRepository,
)
from app.infra.repositories.mongodb.mongodb_metadata_repository import (
    MongoDBMetadataRepository,
)
from app.infra.services.inmemory.stub_ocr_service import StubOCRService
from app.ports.image_downloader_service import ImageDownloaderService
from app.services.image_service import (
    InMemoryImageRepository,
    InMemoryMetadataRepository,
)
from app.usecases.predict_usecase import PredictUsecase
from app.webservice import app, create_app


class MockUploadFile:
    """Mocking an upload file."""

    def __init__(self, content, content_type, filename):
        """Init the mock."""
        self.content = content
        self.content_type = content_type
        self.filename = filename


class _PredictInput(BaseModel):
    """Mocking an input."""

    action: str


class _PredictOutput(BaseModel):
    """Mocking an output."""

    status: str


async def _predict(item: _PredictInput) -> _PredictOutput:
    """Mocking a prediction."""
    if item.action == "SuccessfulResponse":
        return _PredictOutput(status="Success")
    elif item.action == "BaseAPIException":
        raise BaseAPIException("This is a BaseAPIException raised for testing.")
    else:
        raise Exception("This is an unknown exception raised for testing.")


@pytest.fixture(name="client")
def app_client_fixture():
    """Use the real FastAPI app for testing."""
    client = TestClient(app)
    return client


def test_base_routes_of_create_app(client):
    """Test the health and root endpoints."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    response = client.get("/")
    assert response.status_code == 200


def test_base_exceptions_str_representation():
    """Test the string representation of BaseAPIException."""
    exc = BaseAPIException("Test error")
    assert (
        str(exc)
        == "[status_code=500][title=internal server error][details=Test error]"
    )


def test_base_api_exception_response():
    """Test the response() method of BaseAPIException."""
    exc = BaseAPIException("Test error response")
    response = exc.response()

    assert response.status_code == 500
    assert json.loads(response.body.decode()) == {
        "details": "Test error response",
        "status_code": 500,
        "title": "internal server error",
    }


def test_base_api_exception_response_model():
    """Test the response_model() classmethod of BaseAPIException."""
    response_model = BaseAPIException.response_model()

    assert 500 in response_model
    assert "model" in response_model[500]
    assert response_model[500]["model"] == BaseAPIException.pydantic_model


def test_predict():
    """Test the predict endpoint returns a valid prediction when DI is configured."""

    class StubDownloader(ImageDownloaderService):
        """Stub downloader returning fixed bytes."""

        def download(self, source_url: str) -> bytes:
            """Return fake image bytes."""
            return b"fake_image_data"

    test_app = create_app(
        ocr_service=StubOCRService(),
        image_repository=InMemoryImageRepository(),
        metadata_repository=InMemoryMetadataRepository(),
        image_downloader_service=StubDownloader(),
    )
    test_client = TestClient(test_app)

    response = test_client.post(
        "/predict",
        json={"url": "https://example.com/image.jpg"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "predicted_text" in data
    assert "score" in data
    assert "score" in data
    assert len(data["predicted_text"]) == 15
    assert 0.5 <= data["score"] <= 1.0


def test_create_app_wires_predict_usecase_with_stub_ocr_by_default() -> None:
    """Ensure create_app wires PredictUsecase with StubOCRService by default."""
    test_app = create_app()

    assert isinstance(test_app.state.predict_usecase, PredictUsecase)
    assert isinstance(test_app.state.predict_usecase.ocr_service, StubOCRService)


def test_create_app_uses_inmemory_repositories_by_default(monkeypatch) -> None:
    """Ensure default mode uses in-memory repositories for isolated tests."""
    monkeypatch.delenv("APP_DEPENDENCY_MODE", raising=False)

    test_app = create_app()

    assert isinstance(
        test_app.state.predict_usecase.image_repository,
        InMemoryImageRepository,
    )
    assert isinstance(
        test_app.state.predict_usecase.metadata_repository,
        InMemoryMetadataRepository,
    )


def test_create_app_uses_production_repositories_when_mode_production(
    monkeypatch,
) -> None:
    """Ensure production mode wires real infrastructure repositories."""
    monkeypatch.setenv("APP_DEPENDENCY_MODE", "production")

    test_app = create_app()

    assert isinstance(
        test_app.state.predict_usecase.image_repository,
        MinioImageRepository,
    )
    assert isinstance(
        test_app.state.predict_usecase.metadata_repository,
        MongoDBMetadataRepository,
    )


def test_is_truthy_with_truthy_values() -> None:
    """Test _is_truthy function with various truthy values."""
    from app.webservice import _is_truthy

    assert _is_truthy("1") is True
    assert _is_truthy("true") is True
    assert _is_truthy("yes") is True
    assert _is_truthy("on") is True
    assert _is_truthy("TRUE") is True
    assert _is_truthy("YES") is True
    assert _is_truthy("ON") is True


def test_is_truthy_with_falsy_values() -> None:
    """Test _is_truthy function with falsy values."""
    from app.webservice import _is_truthy

    assert _is_truthy(None) is False
    assert _is_truthy("0") is False
    assert _is_truthy("false") is False
    assert _is_truthy("no") is False
    assert _is_truthy("off") is False
    assert _is_truthy("") is False
    assert _is_truthy("random") is False


def test_metrics_endpoint(client) -> None:
    """Test the /metrics endpoint returns Prometheus metrics."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert b"ocr_prediction_score_avg" in response.content
    assert b"ocr_predictions_total" in response.content


def test_create_app_raises_error_when_only_image_repository_provided() -> None:
    """Test create_app raises ValueError when only image_repository is provided."""
    with pytest.raises(ValueError) as exc_info:
        create_app(
            image_repository=InMemoryImageRepository(),
            metadata_repository=None,
        )
    assert (
        "image_repository and metadata_repository must be both provided or both omitted"
        in str(exc_info.value)
    )


def test_create_app_raises_error_when_only_metadata_repository_provided() -> None:
    """Test create_app raises ValueError when only metadata_repository is provided."""
    with pytest.raises(ValueError) as exc_info:
        create_app(
            image_repository=None,
            metadata_repository=InMemoryMetadataRepository(),
        )
    assert (
        "image_repository and metadata_repository must be both provided or both omitted"
        in str(exc_info.value)
    )


def test_get_registry_returns_prometheus_registry() -> None:
    """Test that get_registry returns the Prometheus metrics registry."""
    from app.infra.services.prometheus_metrics import get_registry

    registry = get_registry()
    assert registry is not None
    # Verify it's a Prometheus CollectorRegistry
    assert hasattr(registry, "collect")
