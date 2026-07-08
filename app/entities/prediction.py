"""Domain entities representing core business concepts."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Prediction(BaseModel):
    """Immutable entity representing an OCR prediction result.

    Attributes:
        predicted_text: The text predicted by the OCR model.
        confidence_score: Confidence score of the prediction (0.0-1.0).
    """

    predicted_text: str = Field(..., min_length=1)
    confidence_score: float = Field(ge=0.0, le=1.0)

    model_config = ConfigDict(frozen=True)

class PredictionMetadata(BaseModel):
    """Immutable entity representing metadata for a prediction.

    Attributes:
        timestamp: When the prediction was made (UTC).
        source_url: Original URL of the image.
        image_path: Path where image is stored (MinIO).
        annotation: Optional human annotation for validation.
    """

    timestamp: datetime
    source_url: str = Field(..., min_length=1)
    image_path: str = Field(..., min_length=1)
    annotation: Optional[str] = None

    model_config = ConfigDict(frozen=True)

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: datetime) -> datetime:
        """Validate that timestamp is timezone-aware (UTC)."""
        if v.tzinfo is None:
            msg = "Timestamp must be timezone-aware (UTC)"
            raise ValueError(msg)
        return v


class PredictionRecord(BaseModel):
    """Immutable entity representing a complete prediction record.

    Aggregates prediction result with its metadata.

    Attributes:
        prediction: The prediction result.
        metadata: Metadata associated with the prediction.
    """

    prediction: Prediction
    metadata: PredictionMetadata

    model_config = ConfigDict(frozen=True)
