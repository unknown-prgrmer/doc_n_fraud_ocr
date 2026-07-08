"""Ports (interfaces) for external dependencies."""

from abc import ABC, abstractmethod

from app.entities.prediction import Prediction
from app.ports.image_downloader_service import ImageDownloaderService
from app.ports.image_repository import ImageRepository
from app.ports.metadata_repository import MetadataRepository

__all__ = ["ImageDownloaderService", "ImageRepository", "MetadataRepository", "OCRService"]


class OCRService(ABC):
    """Port for OCR prediction service."""

    @abstractmethod
    def predict(self, image_data: bytes) -> Prediction:
        """Make an OCR prediction on image data.

        Args:
            image_data: Raw image bytes.

        Returns:
            Prediction entity with predicted text and confidence score.

        Raises:
            ValueError: If prediction fails.
        """
