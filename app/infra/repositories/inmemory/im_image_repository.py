"""Adapter implementations (concrete implementations of ports)."""

import logging
import uuid
from typing import Dict

from app.ports.image_repository import ImageRepository

logger = logging.getLogger(__name__)


class InMemoryImageRepository(ImageRepository):
    """In-memory implementation of ImageRepository.

    Stores images in a dictionary. Useful for testing without
    actual MinIO/S3 infrastructure.
    """

    def __init__(self) -> None:
        """Initialize the repository."""
        self._storage: Dict[str, bytes] = {}

    def store(self, image_data: bytes) -> str:
        """Store image and return path.

        Args:
            image_data: Raw image bytes.

        Returns:
            Path where image was stored (UUID-based).
        """
        path = f"memory://{uuid.uuid4()}.jpg"
        self._storage[path] = image_data
        logger.debug("Image stored in memory: %s", path)
        return path

    def retrieve(self, path: str) -> bytes:
        """Retrieve stored image by path.

        Args:
            path: Path to retrieve.

        Returns:
            Image bytes.

        Raises:
            KeyError: If path not found.
        """
        if path not in self._storage:
            msg = f"Image not found: {path}"
            raise KeyError(msg)
        return self._storage[path]
