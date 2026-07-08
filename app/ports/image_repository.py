"""Ports (interfaces) for external dependencies."""

from abc import ABC, abstractmethod


class ImageRepository(ABC):
    """Port for image storage (e.g., MinIO, S3)."""

    @abstractmethod
    def store(self, image_data: bytes) -> str:
        """Store image and return its path.

        Args:
            image_data: Raw image bytes to store.

        Returns:
            Path where image was stored (e.g., "s3://bucket/path").

        Raises:
            IOError: If storage fails.
        """
