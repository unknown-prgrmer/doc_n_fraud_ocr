"""Adapter implementations (concrete implementations of ports)."""

import logging

import httpx

from app.ports.image_downloader_service import ImageDownloaderService

logger = logging.getLogger(__name__)

class HttpImageDownloaderService(ImageDownloaderService):
    """HTTP implementation of the image downloader port."""

    def __init__(self, http_client: httpx.Client | None = None) -> None:
        """Initialize downloader with optional injected HTTP client."""
        self._http_client = http_client or httpx.Client()

    def download(self, source_url: str) -> bytes:
        """Download image bytes from a URL."""
        try:
            response = self._http_client.get(source_url, timeout=10.0)
            response.raise_for_status()
            return response.content
        except (httpx.InvalidURL, httpx.UnsupportedProtocol) as error:
            raise ValueError(f"Invalid URL: {source_url}") from error
        except httpx.HTTPError as error:
            raise IOError(f"Download failed for {source_url}: {error}") from error
