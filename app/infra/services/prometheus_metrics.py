"""Prometheus metrics for OCR prediction service."""

from prometheus_client import CollectorRegistry, Counter, Gauge

# Create a global registry for metrics
_registry = CollectorRegistry()

# Gauge for average prediction score
prediction_score_gauge = Gauge(
    'ocr_prediction_score_avg',
    'Average OCR prediction confidence score',
    registry=_registry,
)

# Gauge for predictions per minute
predictions_per_minute_gauge = Gauge(
    'ocr_predictions_per_minute',
    'Number of OCR predictions per minute',
    registry=_registry,
)

# Counter for low confidence predictions (< 0.5)
low_confidence_counter = Counter(
    'ocr_low_confidence_predictions_total',
    'Total number of OCR predictions with confidence score below threshold (0.5)',
    registry=_registry,
)

# Counter for total predictions
total_predictions_counter = Counter(
    'ocr_predictions_total',
    'Total number of OCR predictions made',
    registry=_registry,
)


def get_registry():
    """Get the Prometheus metrics registry."""
    return _registry
