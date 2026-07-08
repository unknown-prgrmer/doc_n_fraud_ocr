"""Ports (interfaces) for external dependencies."""

from abc import ABC, abstractmethod

from app.entities.prediction import Prediction, PredictionMetadata


class MetadataRepository(ABC):
    """Port for metadata storage (e.g., MongoDB)."""

    @abstractmethod
    def save(self, metadata: PredictionMetadata, prediction: Prediction) -> None:
        """Persist prediction metadata and result.

        Args:
            metadata: Metadata entity to persist.
            prediction: Prediction result to persist.

        Raises:
            RuntimeError: If persistence fails.
        """
