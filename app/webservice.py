"""Base API."""

import os
import typing as tp

from fastapi import FastAPI, status
from fastapi.responses import Response
from prometheus_client import generate_latest

from app.infra.fastapi.router.health import health
from app.infra.fastapi.router.prediction import predict
from app.infra.fastapi.router.root import root
from app.infra.fastapi.schemas.schemas import HealthCheckResponse, PredictOutput
from app.infra.repositories.inmemory.im_image_repository import (
    InMemoryImageRepository,
)
from app.infra.repositories.inmemory.im_metadata_repository import (
    InMemoryMetadataRepository,
)
from app.infra.repositories.minio.minio_image_repository import (
    MinioImageRepository,
)
from app.infra.repositories.mongodb.mongodb_metadata_repository import (
    MongoDBMetadataRepository,
)
from app.infra.services.http.image_downloader_service import (
    HttpImageDownloaderService,
)
from app.infra.services.inmemory.stub_ocr_service import StubOCRService
from app.infra.services.prometheus_metrics import get_registry
from app.ports.image_downloader_service import ImageDownloaderService
from app.ports.image_repository import ImageRepository
from app.ports.metadata_repository import MetadataRepository
from app.ports.ocr_service import OCRService
from app.usecases.predict_usecase import PredictUsecase


def _is_truthy(value: str | None) -> bool:
    """Return True when a string env value represents truth."""
    if value is None:
        return False
    return value.lower() in {"1", "true", "yes", "on"}


def _build_default_repositories(
) -> tuple[ImageRepository, MetadataRepository]:
    """Build default repositories from environment configuration.

    The app uses in-memory repositories by default to keep local tests
    isolated from external services.
    """
    mode = os.getenv("APP_DEPENDENCY_MODE", "inmemory").lower()
    if mode == "production":
        minio_secure = _is_truthy(os.getenv("MINIO_SECURE", "false"))
        image_repository = MinioImageRepository(
            endpoint=os.getenv("MINIO_ENDPOINT", "minio:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            bucket_name=os.getenv("MINIO_BUCKET", "ocr-images"),
            secure=minio_secure,
        )
        metadata_repository = MongoDBMetadataRepository(
            connection_string=os.getenv("MONGODB_URI", "mongodb://mongo:27017/"),
            database_name=os.getenv("MONGODB_DATABASE", "ocr_pipeline"),
            collection_name=os.getenv("MONGODB_COLLECTION", "predictions"),
        )
        return image_repository, metadata_repository

    return InMemoryImageRepository(), InMemoryMetadataRepository()


def add_base_routes(
    source_app: FastAPI,
) -> None:
    """Add basic routes to a FastAPI app.

    added routes are:
      - '/health' => return {'status': 'ok'}
      - '/' => redirect to '/docs'
      - '/predict' => run OCR prediction from image URL
      - '/metrics' => Prometheus metrics endpoint

    Args:
        source_app: instance of a FastAPI application
    """
    # make sure we have a FastAPI app :)
    assert isinstance(source_app, FastAPI)

    # add basic health check route
    source_app.add_api_route(
        "/health",
        health,
        status_code=status.HTTP_200_OK,
        include_in_schema=True,
        response_model=HealthCheckResponse,
    )

    # add redirect route to /docs
    # not included in openAPI schema
    source_app.add_api_route(
        "/",
        root,
        include_in_schema=False,
    )

    source_app.add_api_route(
        "/predict",
        predict,
        methods=["POST"],
        include_in_schema=True,
        response_model=PredictOutput,
    )

    # add Prometheus metrics endpoint
    async def metrics():
        """Return Prometheus metrics."""
        return Response(
            content=generate_latest(get_registry()),
            media_type="text/plain; charset=utf-8",
        )

    source_app.add_api_route(
        "/metrics",
        metrics,
        methods=["GET"],
        include_in_schema=False,
    )


def create_app(
    debug: bool = False,
    title: str = "FastAPI",
    description: str = "FastAPI app",
    ocr_service: tp.Optional[OCRService] = None,
    image_repository: tp.Optional[ImageRepository] = None,
    metadata_repository: tp.Optional[MetadataRepository] = None,
    image_downloader_service: tp.Optional[ImageDownloaderService] = None,
    **kwargs: tp.Any,
) -> FastAPI:
    """Create a FastAPI application with basic routes.

    Args:
        debug: Run the app in debug mode. Defaults to False.
        title: Defaults to "FastAPI".
        description: Defaults to "FastAPI app".
        ocr_service: OCR prediction service (port).
        image_repository: Image storage repository (port).
        metadata_repository: Metadata persistence repository (port).
        image_downloader_service: Image download service (port).
        kwargs: other keyword arguments to pass to FastAPI app.

    Returns:
        The FastAPI app ready to be used or extended.
    """
    # FastAPI instance
    new_app = FastAPI(
        debug=debug,
        title=title,
        version="0.1.0",
        description=description,
        **kwargs,
    )

    resolved_ocr_service = ocr_service or StubOCRService()
    resolved_image_downloader_service = (
        image_downloader_service or HttpImageDownloaderService()
    )

    if image_repository is None and metadata_repository is None:
        resolved_image_repository, resolved_metadata_repository = (
            _build_default_repositories()
        )
    elif image_repository is not None and metadata_repository is not None:
        resolved_image_repository = image_repository
        resolved_metadata_repository = metadata_repository
    else:
        msg = (
            "image_repository and metadata_repository must be both provided or "
            "both omitted"
        )
        raise ValueError(msg)

    # Wire dependencies into app state for request-time access
    new_app.state.image_downloader_service = resolved_image_downloader_service
    new_app.state.predict_usecase = PredictUsecase(
        ocr_service=resolved_ocr_service,
        image_repository=resolved_image_repository,
        metadata_repository=resolved_metadata_repository,
    )

    add_base_routes(new_app)
    return new_app


app = create_app(
    title="webservice",
    description="Service to run application.",
)
