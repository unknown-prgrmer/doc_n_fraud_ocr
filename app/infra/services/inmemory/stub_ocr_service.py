"""Adapter implementations (concrete implementations of ports)."""

import logging
import random
import string

from app.entities.prediction import Prediction
from app.ports.ocr_service import (
    OCRService,
)

logger = logging.getLogger(__name__)


class StubOCRService(OCRService):
    """Stub OCR service that returns random predictions.

    Used for development and testing when real OCR is not available.
    """

    def predict(self, image_data: bytes) -> Prediction:
        """Generate a random prediction for demonstration.

        Args:
            image_data: Raw image bytes.

        Returns:
            Prediction with random text and confidence score.

        Raises:
            ValueError: If image_data is empty.
        """
        if not image_data:
            msg = "Image data cannot be empty"
            raise ValueError(msg)

        # Generate random predicted text (15 characters)
        predicted_text = "".join(
            random.choices(string.ascii_letters + string.digits, k=15)
        )

        # Generate random confidence score between 0.5 and 1.0
        confidence_score = round(random.uniform(0.5, 1.0), 2)

        logger.debug(
            "Stub OCR prediction: text=%s, score=%.2f",
            predicted_text,
            confidence_score,
        )

        return Prediction(
            predicted_text=predicted_text,
            confidence_score=confidence_score,
        )
