"""Tests for MongoDB metadata repository adapter."""

from datetime import datetime, timezone

import pytest
from pymongo.errors import PyMongoError

from app.entities.prediction import Prediction, PredictionMetadata
from app.infra.repositories.mongodb.mongodb_metadata_repository import (
    MongoClientProtocol,
    MongoDBMetadataRepository,
)


class _FakeInsertResult:
    """Fake MongoDB insert result."""

    def __init__(self, acknowledged: bool) -> None:
        """Initialize acknowledgement behavior."""
        self.acknowledged = acknowledged


class _FakeCollection:
    """Fake MongoDB collection."""

    def __init__(self) -> None:
        """Initialize fake collection state."""
        self.documents: list[dict] = []
        self.raise_error = False
        self.acknowledged = True

    def insert_one(self, document: dict) -> _FakeInsertResult:
        """Insert document into fake collection."""
        if self.raise_error:
            raise PyMongoError("mongo failure")
        self.documents.append(document)
        return _FakeInsertResult(self.acknowledged)


class _FakeDatabase:
    """Fake MongoDB database."""

    def __init__(self, collection: _FakeCollection) -> None:
        """Initialize fake database state."""
        self._collection = collection

    def __getitem__(self, collection_name: str) -> _FakeCollection:
        """Return fake collection."""
        return self._collection


class _FakeMongoClient(MongoClientProtocol):
    """Fake MongoDB client."""

    def __init__(self, database: _FakeDatabase) -> None:
        """Initialize fake mongo client."""
        self._database = database

    def __getitem__(self, key: str) -> _FakeDatabase:
        """Return fake database."""
        return self._database


class TestMongoDBMetadataRepository:
    """Test cases for MongoDBMetadataRepository."""

    def test_save_persists_expected_document(self) -> None:
        """Persist source URL, image path, timestamp and prediction data."""
        collection = _FakeCollection()
        client: MongoClientProtocol = _FakeMongoClient(_FakeDatabase(collection))
        repository = MongoDBMetadataRepository(
            connection_string="mongodb://ignored",
            database_name="ocr_pipeline",
            collection_name="predictions",
            client=client,
        )
        metadata = PredictionMetadata(
            timestamp=datetime.now(timezone.utc),
            source_url="https://example.com/image.jpg",
            image_path="s3://ocr-images/example.jpg",
            annotation="verified",
        )
        prediction = Prediction(predicted_text="hello", confidence_score=0.91)

        repository.save(metadata, prediction)

        assert len(collection.documents) == 1
        document = collection.documents[0]
        assert document["source_url"] == metadata.source_url
        assert document["image_path"] == metadata.image_path
        assert document["annotation"] == metadata.annotation
        assert document["prediction"]["predicted_text"] == prediction.predicted_text
        assert (
            document["prediction"]["confidence_score"] == prediction.confidence_score
        )

    def test_save_when_not_acknowledged_raises_runtime_error(self) -> None:
        """Raise RuntimeError when MongoDB write is not acknowledged."""
        collection = _FakeCollection()
        collection.acknowledged = False
        client: MongoClientProtocol = _FakeMongoClient(_FakeDatabase(collection))
        repository = MongoDBMetadataRepository(
            connection_string="mongodb://ignored",
            database_name="ocr_pipeline",
            collection_name="predictions",
            client=client,
        )
        metadata = PredictionMetadata(
            timestamp=datetime.now(timezone.utc),
            source_url="https://example.com/image.jpg",
            image_path="s3://ocr-images/example.jpg",
        )
        prediction = Prediction(predicted_text="hello", confidence_score=0.91)

        with pytest.raises(RuntimeError, match="did not acknowledge"):
            repository.save(metadata, prediction)

    def test_save_when_mongo_fails_raises_runtime_error(self) -> None:
        """Map PyMongo errors to RuntimeError."""
        collection = _FakeCollection()
        collection.raise_error = True
        client: MongoClientProtocol = _FakeMongoClient(_FakeDatabase(collection))
        repository = MongoDBMetadataRepository(
            connection_string="mongodb://ignored",
            database_name="ocr_pipeline",
            collection_name="predictions",
            client=client,
        )
        metadata = PredictionMetadata(
            timestamp=datetime.now(timezone.utc),
            source_url="https://example.com/image.jpg",
            image_path="s3://ocr-images/example.jpg",
        )
        prediction = Prediction(predicted_text="hello", confidence_score=0.91)

        with pytest.raises(RuntimeError, match="Failed to persist prediction metadata"):
            repository.save(metadata, prediction)
