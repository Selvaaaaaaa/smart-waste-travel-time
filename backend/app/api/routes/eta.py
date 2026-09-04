import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.eta_service import ETAService
from app.services.hybrid_eta_service import HybridETAService
from app.schemas.ml import ETAPredictRequest, ETAPredictResponse, HybridPredictRequest, HybridPredictResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/eta", tags=["ETA Prediction"])


@router.post("/predict", response_model=ETAPredictResponse)
def predict_eta(
    req: ETAPredictRequest,
    db: Session = Depends(get_db),
):
    """
    Predict travel time for waste collection route under given environmental and operational context.
    Returns both the deterministic baseline ETA and the context-aware ML prediction.
    """
    try:
        result = ETAService.predict_both(
            params=req.model_dump(),
            db=db,
            route_id=req.route_id,
            persist=req.persist,
        )
        return ETAPredictResponse(**result)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )
    except RuntimeError as re:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(re),
        )
    except Exception as e:
        logger.exception("ETA prediction failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction error: {str(e)}",
        )


@router.post("/hybrid", response_model=HybridPredictResponse)
def predict_hybrid_eta(
    req: HybridPredictRequest,
    db: Session = Depends(get_db),
):
    """
    Predict travel time using the Adaptive Hybrid ETA strategy.
    Performs safety validation -> pre-trip rule selection -> ETA prediction.
    """
    try:
        result = HybridETAService.predict_hybrid(
            params=req.model_dump(),
            db=db,
            route_id=req.route_id,
            persist=req.persist,
        )
        return HybridPredictResponse(**result)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )
    except RuntimeError as re:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(re),
        )
    except Exception as e:
        logger.exception("Hybrid ETA prediction failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction error: {str(e)}",
        )
