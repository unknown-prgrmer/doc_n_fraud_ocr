"""Tests for MinIO image repository adapter."""

import pytest
from minio.error import MinioException

from app.infra.repositories.minio.minio_image_repository import (
    MinioClientProtocol,
    MinioImageRepository,
)


class _FakeMinioClient:
    """Fake MinIO client for unit tests."""

    def __init__(self, bucket_exists: bool = False) -> None:
        """Initialize fake client behavior."""
        self._bucket_exists = bucket_exists
        self.bucket_exists_calls = 0
        self.make_bucket_calls = 0
        self.put_calls = 0
        self.fail_bucket_check = False
        self.fail_put = False

    def bucket_exists(self, bucket_name: str) -> bool:
        """Return configured bucket existence."""
        self.bucket_exists_calls += 1
        if self.fail_bucket_check:
            raise MinioException("bucket check failed")
        return self._bucket_exists

    def make_bucket(self, bucket_name: str) -> None:
        """Record bucket creation."""
        self.make_bucket_calls += 1
        self._bucket_exists = True

    def put_object(
        self,
        bucket_name: str,
        object_name: str,
        data: object,
        length: int,
        content_type: str,
    ) -> None:
        """Store object invocation or fail."""
        self.put_calls += 1
        if self.fail_put:
            raise MinioException("put failed")


class TestMinioImageRepository:
    """Test cases for MinioImageRepository."""

    def test_store_creates_bucket_once_and_returns_path(self) -> None:
        """Create bucket once and return S3-like path."""
        client: MinioClientProtocol = _FakeMinioClient(bucket_exists=False)
        repository = MinioImageRepository(
            endpoint="minio:9000",
            access_key="key",
            secret_key="secret",
            bucket_name="ocr-images",
            client=client,
        )

        first_path = repository.store(b"image-one")
        second_path = repository.store(b"image-two")

        assert first_path.startswith("s3://ocr-images/")
        assert second_path.startswith("s3://ocr-images/")
        assert first_path != second_path
        assert client.bucket_exists_calls == 1
        assert client.make_bucket_calls == 1
        assert client.put_calls == 2

    def test_store_with_empty_payload_raises_io_error(self) -> None:
        """Reject empty payloads."""
        client: MinioClientProtocol = _FakeMinioClient(bucket_exists=True)
        repository = MinioImageRepository(
            endpoint="minio:9000",
            access_key="key",
            secret_key="secret",
            bucket_name="ocr-images",
            client=client,
        )

        with pytest.raises(IOError, match="Image data cannot be empty"):
            repository.store(b"")

    def test_store_when_bucket_check_fails_raises_io_error(self) -> None:
        """Map MinIO bucket errors to IOError."""
        client: MinioClientProtocol = _FakeMinioClient(bucket_exists=True)
        client.fail_bucket_check = True
        repository = MinioImageRepository(
            endpoint="minio:9000",
            access_key="key",
            secret_key="secret",
            bucket_name="ocr-images",
            client=client,
        )

        with pytest.raises(IOError, match="Failed to validate MinIO bucket"):
            repository.store(b"image-data")

    def test_store_when_upload_fails_raises_io_error(self) -> None:
        """Map MinIO upload errors to IOError."""
        client: MinioClientProtocol = _FakeMinioClient(bucket_exists=True)
        client.fail_put = True
        repository = MinioImageRepository(
            endpoint="minio:9000",
            access_key="key",
            secret_key="secret",
            bucket_name="ocr-images",
            client=client,
        )

        with pytest.raises(IOError, match="Failed to store image in MinIO bucket"):
            repository.store(b"image-data")
