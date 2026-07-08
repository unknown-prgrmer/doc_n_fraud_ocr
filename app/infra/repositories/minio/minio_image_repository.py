"""MinIO repository implementation for image storage."""

from __future__ import annotations

import io
import logging
import uuid
from typing import Protocol

from app.ports.image_repository import ImageRepository
from minio import Minio
from minio.error import MinioException

logger = logging.getLogger(__name__)


class MinioClientProtocol(Protocol):
    """Protocol defining MinIO client interface for dependency injection."""

    def bucket_exists(self, bucket_name: str) -> bool:
        """Return whether a bucket exists."""
        ...

    def make_bucket(self, bucket_name: str) -> None:
        """Create a bucket."""
        ...

    def put_object(
        self,
        bucket_name: str,
        object_name: str,
        data: object,
        length: int,
        content_type: str,
    ) -> object:
        """Upload an object."""
        ...


class MinioImageRepository(ImageRepository):
    """Store images in MinIO."""

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        secure: bool = False,
        client: MinioClientProtocol | None = None,
    ) -> None:
        """Initialize MinIO repository.

        Args:
            endpoint: MinIO endpoint (host:port).
            access_key: MinIO access key.
            secret_key: MinIO secret key.
            bucket_name: Target bucket name.
            secure: Use HTTPS when True.
            client: Optional injected MinIO client satisfying MinioClientProtocol.
        """
        self._bucket_name = bucket_name
        self._client = client or Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
        self._bucket_checked = False

    def _ensure_bucket(self) -> None:
        """Create the bucket when it does not exist."""
        if self._bucket_checked:
            return

        try:
            if not self._client.bucket_exists(self._bucket_name):
                self._client.make_bucket(self._bucket_name)
                logger.info("Created MinIO bucket: %s", self._bucket_name)
            self._bucket_checked = True
        except MinioException as error:
            msg = f"Failed to validate MinIO bucket {self._bucket_name}"
            logger.exception(msg)
            raise IOError(msg) from error

    def store(self, image_data: bytes) -> str:
        """Store image bytes and return an S3-like URI path."""
        if not image_data:
            msg = "Image data cannot be empty"
            raise IOError(msg)

        self._ensure_bucket()

        object_name = f"{uuid.uuid4()}.jpg"
        payload = io.BytesIO(image_data)

        try:
            self._client.put_object(
                bucket_name=self._bucket_name,
                object_name=object_name,
                data=payload,
                length=len(image_data),
                content_type="image/jpeg",
            )
        except MinioException as error:
            msg = f"Failed to store image in MinIO bucket {self._bucket_name}"
            logger.exception(msg)
            raise IOError(msg) from error

        image_path = f"s3://{self._bucket_name}/{object_name}"
        logger.info("Image stored in MinIO at %s", image_path)
        return image_path
