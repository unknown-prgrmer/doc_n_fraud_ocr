"""Usecases layer (application business rules)."""

import logging
from datetime import datetime, timezone
from typing import Optional

from app.entities.prediction import PredictionMetadata, PredictionRecord
from app.infra.services.prometheus_metrics import (
    low_confidence_counter,
    prediction_score_gauge,
    total_predictions_counter,
)
from app.ports.image_repository import ImageRepository
from app.ports.metadata_repository import MetadataRepository
from app.ports.ocr_service import OCRService

logger = logging.getLogger(__name__)


class PredictUsecase:
    """Usecase for making OCR predictions on images.

    Orchestrates the flow of:
    1. OCR prediction via service
    2. Image storage via repository
    3. Metadata persistence via repository
    """

    def __init__(
        self,
        ocr_service: OCRService,
        image_repository: ImageRepository,
        metadata_repository: MetadataRepository,
    ) -> None:
        """Initialize the prediction usecase.

        Args:
            ocr_service: Service for OCR predictions (port).
            image_repository: Repository for storing images (port).
            metadata_repository: Repository for storing metadata (port).
        """
        self.ocr_service = ocr_service
        self.image_repository = image_repository
        self.metadata_repository = metadata_repository

    def predict_from_image_data(
        self,
        image_data: bytes,
        source_url: str,
        annotation: Optional[str] = None,
    ) -> PredictionRecord:
        """Make a prediction from image data and persist results.

        Process:
        1. Call OCR service to get prediction
        2. Store image to repository
        3. Save metadata with prediction result

        Args:
            image_data: Raw image bytes.
            source_url: Original URL of the image (for regulatory requirement).
            annotation: Optional human annotation for validation.

        Returns:
            PredictionRecord containing prediction and metadata.

        Raises:
            ValueError: If OCR prediction fails.
            IOError: If image storage fails.
            RuntimeError: If metadata persistence fails.
        """
        logger.info(
            "Starting prediction for image from %s",
            source_url,
        )

        # Step 1: Get OCR prediction (may raise ValueError)
        prediction = self.ocr_service.predict(image_data)
        logger.debug(
            "OCR prediction obtained: %s (score=%.2f)",
            prediction.predicted_text,
            prediction.confidence_score,
        )

        # Step 2: Store image (may raise IOError)
        image_path = self.image_repository.store(image_data)
        logger.debug("Image stored at: %s", image_path)

        # Step 3: Create and persist metadata (may raise RuntimeError)
        now = datetime.now(timezone.utc)
        metadata = PredictionMetadata(
            timestamp=now,
            source_url=source_url,
            image_path=image_path,
            annotation=annotation,
        )
        self.metadata_repository.save(metadata, prediction)
        logger.debug("Metadata persisted for image: %s", image_path)

        # Update Prometheus metrics
        total_predictions_counter.inc()
        prediction_score_gauge.set(prediction.confidence_score)
        if prediction.confidence_score < 0.5:
            low_confidence_counter.inc()

        # Return the complete record
        record = PredictionRecord(prediction=prediction, metadata=metadata)
        logger.info("Prediction completed successfully for %s", source_url)
        return record
