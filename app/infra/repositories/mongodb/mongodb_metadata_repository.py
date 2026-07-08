"""MongoDB repository implementation for prediction metadata."""

from __future__ import annotations

import logging
from typing import Any, Protocol

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.entities.prediction import Prediction, PredictionMetadata
from app.ports.metadata_repository import MetadataRepository


class MongoClientProtocol(Protocol):
    """Protocol defining MongoClient interface for dependency injection."""

    def __getitem__(self, key: str) -> Any:
        """Get database by name."""
        ...


logger = logging.getLogger(__name__)


class MongoDBMetadataRepository(MetadataRepository):
    """Persist prediction metadata and scores into MongoDB."""

    def __init__(
        self,
        connection_string: str,
        database_name: str,
        collection_name: str,
        client: MongoClientProtocol | None = None,
    ) -> None:
        """Initialize MongoDB metadata repository.

        Args:
            connection_string: MongoDB URI.
            database_name: Database name.
            collection_name: Collection used for prediction records.
            client: Optional injected Mongo client satisfying MongoClientProtocol.
        """
        self._client = client or MongoClient(connection_string, tz_aware=True)
        self._collection = self._client[database_name][collection_name]

    def save(self, metadata: PredictionMetadata, prediction: Prediction) -> None:
        """Persist prediction metadata and result."""
        document = {
            "timestamp": metadata.timestamp,
            "source_url": metadata.source_url,
            "image_path": metadata.image_path,
            "annotation": metadata.annotation,
            "prediction": {
                "predicted_text": prediction.predicted_text,
                "confidence_score": prediction.confidence_score,
            },
        }

        try:
            result = self._collection.insert_one(document)
        except PyMongoError as error:
            msg = "Failed to persist prediction metadata in MongoDB"
            logger.exception(msg)
            raise RuntimeError(msg) from error

        if result.acknowledged is not True:
            msg = "MongoDB did not acknowledge metadata write"
            logger.error(msg)
            raise RuntimeError(msg)

        logger.info(
            "Prediction metadata persisted in MongoDB for %s",
            metadata.source_url,
        )
