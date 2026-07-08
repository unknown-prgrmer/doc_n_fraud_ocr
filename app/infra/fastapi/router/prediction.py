"""Predict endpoint handler."""

import logging
import typing as tp

from fastapi import HTTPException, Request

from app.infra.fastapi.schemas.schemas import PredictInput, PredictOutput

logger = logging.getLogger(__name__)


async def predict(request: Request, body: PredictInput) -> tp.Any:
    """Download an image from a URL, run OCR, persist results, and return the prediction."""
    image_downloader = request.app.state.image_downloader_service
    usecase = request.app.state.predict_usecase

    try:
        image_data = image_downloader.download(body.url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except IOError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    try:
        record = usecase.predict_from_image_data(
            image_data=image_data,
            source_url=body.url,
            annotation=body.annotation,
        )
    except IOError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    logger.info("Prediction completed for %s", body.url)
    return PredictOutput(
        predicted_text=record.prediction.predicted_text,
        score=record.prediction.confidence_score,
    )
