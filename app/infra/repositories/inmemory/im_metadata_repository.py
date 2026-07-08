"""Adapter implementations (concrete implementations of ports)."""

import logging
from typing import List

from app.entities.prediction import (
    Prediction,
    PredictionMetadata,
    PredictionRecord,
)
from app.ports.metadata_repository import MetadataRepository

logger = logging.getLogger(__name__)

class InMemoryMetadataRepository(MetadataRepository):
    """In-memory implementation of MetadataRepository.

    Stores metadata and predictions in a list. Useful for testing
    without actual MongoDB infrastructure.
    """

    def __init__(self) -> None:
        """Initialize the repository."""
        self._records: List[PredictionRecord] = []

    def save(self, metadata: PredictionMetadata, prediction: Prediction) -> None:
        """Persist prediction metadata and result.

        Args:
            metadata: Metadata entity to persist.
            prediction: Prediction result to persist.
        """
        record = PredictionRecord(prediction=prediction, metadata=metadata)
        self._records.append(record)
        logger.debug("Record saved: %s", metadata.source_url)

    def get_all(self) -> List[PredictionRecord]:
        """Get all stored records.

        Returns:
            List of all prediction records.
        """
        return self._records.copy()

    def get_by_source_url(self, source_url: str) -> List[PredictionRecord]:
        """Get records filtered by source URL.

        Args:
            source_url: URL to filter by.

        Returns:
            List of matching records.
        """
        return [
            record for record in self._records
            if record.metadata.source_url == source_url
        ]
