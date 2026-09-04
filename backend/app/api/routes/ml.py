import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.ml.model_registry import is_model_available, get_model_metadata
from app.ml.train import train_and_evaluate
from app.schemas.ml import MLTrainRequest, MLTrainResponse, MLStatusResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ml", tags=["Machine Learning"])


@router.get("/status", response_model=MLStatusResponse)
def get_ml_status():
    """
    Retrieve active ML model status, metadata, evaluation metrics, and feature importances.
    Returns is_trained: False if model has not been trained yet.
    """
    if not is_model_available():
        return MLStatusResponse(
            is_trained=False,
            synthetic_disclaimer="Synthetic Dataset — Research Prototype",
        )

    try:
        meta = get_model_metadata()
        return MLStatusResponse(
            is_trained=True,
            model_name=meta.get("model_name"),
            model_type=meta.get("model_type"),
            model_version=meta.get("model_version"),
            training_date=meta.get("training_date"),
            training_row_count=meta.get("training_row_count"),
            testing_row_count=meta.get("testing_row_count"),
            total_dataset_rows=meta.get("total_dataset_rows"),
            metrics=meta.get("metrics"),
            feature_importances=meta.get("feature_importances"),
            split_method=meta.get("split_method"),
            synthetic_disclaimer=meta.get("synthetic_disclaimer", "Synthetic Dataset — Research Prototype"),
        )
    except Exception as e:
        logger.error("Error retrieving ML metadata: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not load ML metadata: {str(e)}",
        )


@router.post("/train", response_model=MLTrainResponse)
def train_model_endpoint(
    req: MLTrainRequest = MLTrainRequest(),
    db: Session = Depends(get_db),
):
    """
    Trigger context-aware machine learning model training on historical observations stored in PostgreSQL / DB.
    Evaluates baseline vs context-aware tree-based models and stores trained weights and metadata.
    """
    logger.info("Received model training request: type=%s, n_estimators=%d", req.model_type, req.n_estimators)
    try:
        meta = train_and_evaluate(
            db=db,
            model_type=req.model_type,
            random_state=req.random_state,
            n_estimators=req.n_estimators,
        )

        status_res = MLStatusResponse(
            is_trained=True,
            model_name=meta.get("model_name"),
            model_type=meta.get("model_type"),
            model_version=meta.get("model_version"),
            training_date=meta.get("training_date"),
            training_row_count=meta.get("training_row_count"),
            testing_row_count=meta.get("testing_row_count"),
            total_dataset_rows=meta.get("total_dataset_rows"),
            metrics=meta.get("metrics"),
            feature_importances=meta.get("feature_importances"),
            split_method=meta.get("split_method"),
            synthetic_disclaimer=meta.get("synthetic_disclaimer", "Synthetic Dataset — Research Prototype"),
        )

        return MLTrainResponse(
            status="SUCCESS",
            message="Model successfully trained and persisted.",
            metadata=status_res,
        )
    except Exception as e:
        logger.exception("Model training failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model training failed: {str(e)}",
        )
