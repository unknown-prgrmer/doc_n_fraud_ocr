"""Health check endpoint handler."""

from app.infra.fastapi.schemas.schemas import HealthCheckResponse


async def health():
    """Simple health-check response."""
    return HealthCheckResponse()
