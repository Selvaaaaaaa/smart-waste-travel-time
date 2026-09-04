import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import joblib
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)

# Base directory for persisted machine learning artifacts
MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "models"
MODEL_FILENAME = "context_aware_eta_model.joblib"
METADATA_FILENAME = "context_aware_eta_metadata.json"

_CACHED_MODEL: Optional[Pipeline] = None
_CACHED_METADATA: Optional[Dict[str, Any]] = None


def get_model_path() -> Path:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    return MODELS_DIR / MODEL_FILENAME


def get_metadata_path() -> Path:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    return MODELS_DIR / METADATA_FILENAME


def is_model_available() -> bool:
    """Check if the serialized model and metadata files exist on disk."""
    return get_model_path().exists() and get_metadata_path().exists()


def save_model(model: Pipeline, metadata: Dict[str, Any]) -> Tuple[Path, Path]:
    """
    Persist trained model pipeline and associated metadata to disk.
    Also updates in-memory model cache.
    """
    global _CACHED_MODEL, _CACHED_METADATA
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    model_path = get_model_path()
    metadata_path = get_metadata_path()

    logger.info("Persisting ML pipeline to %s", model_path)
    joblib.dump(model, model_path)

    logger.info("Persisting ML metadata to %s", metadata_path)
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    _CACHED_MODEL = model
    _CACHED_METADATA = metadata

    return model_path, metadata_path


def load_model(force_reload: bool = False) -> Pipeline:
    """
    Load persisted model pipeline from disk.
    Uses in-memory cache unless force_reload is True.
    Raises FileNotFoundError if model has not been trained yet.
    """
    global _CACHED_MODEL
    if _CACHED_MODEL is not None and not force_reload:
        return _CACHED_MODEL

    model_path = get_model_path()
    if not model_path.exists():
        raise FileNotFoundError(
            f"Context-aware ETA model not found at {model_path}. Please trigger training via POST /api/ml/train or CLI."
        )

    logger.info("Loading model from %s", model_path)
    _CACHED_MODEL = joblib.load(model_path)
    return _CACHED_MODEL


def get_model_metadata(force_reload: bool = False) -> Dict[str, Any]:
    """
    Load metadata dictionary for the active model.
    Raises FileNotFoundError if metadata file does not exist.
    """
    global _CACHED_METADATA
    if _CACHED_METADATA is not None and not force_reload:
        return _CACHED_METADATA

    metadata_path = get_metadata_path()
    if not metadata_path.exists():
        raise FileNotFoundError(
            f"Model metadata not found at {metadata_path}. Model has not been trained yet."
        )

    with open(metadata_path, "r", encoding="utf-8") as f:
        _CACHED_METADATA = json.load(f)

    return _CACHED_METADATA


def extract_feature_importances(pipeline: Pipeline, feature_names: List[str]) -> List[Dict[str, Any]]:
    """
    Extract normalized feature importances from a tree-based model pipeline.
    """
    try:
        regressor = pipeline.named_steps.get("regressor")
        if hasattr(regressor, "feature_importances_"):
            importances = regressor.feature_importances_
            preprocessor = pipeline.named_steps.get("preprocessor")
            
            # Retrieve transformed feature names if possible
            if hasattr(preprocessor, "get_feature_names_out"):
                try:
                    transformed_names = list(preprocessor.get_feature_names_out())
                except Exception:
                    transformed_names = [f"feat_{i}" for i in range(len(importances))]
            else:
                transformed_names = [f"feat_{i}" for i in range(len(importances))]

            # Group or aggregate one-hot categorical features back to high-level features if desirable
            raw_scores = []
            for name, score in zip(transformed_names, importances):
                clean_name = name.replace("num__", "").replace("cat__", "")
                raw_scores.append({"feature": clean_name, "importance": round(float(score), 4)})
            
            # Sort descending by importance
            raw_scores.sort(key=lambda x: x["importance"], reverse=True)
            return raw_scores
    except Exception as e:
        logger.warning("Could not extract feature importances: %s", e)

    return []


def clear_cache() -> None:
    """Clear memory caches (useful during unit tests)."""
    global _CACHED_MODEL, _CACHED_METADATA
    _CACHED_MODEL = None
    _CACHED_METADATA = None
