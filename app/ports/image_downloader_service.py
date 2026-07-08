"""Ports (interfaces) for external dependencies."""

from abc import ABC, abstractmethod


class ImageDownloaderService(ABC):
    """Port for image downloading from URL."""

    @abstractmethod
    def download(self, source_url: str) -> bytes:
        """Download image bytes from a URL.

        Args:
            source_url: URL of the image to download.

        Returns:
            Raw image bytes.

        Raises:
            ValueError: If URL is invalid.
            IOError: If download fails.
        """
