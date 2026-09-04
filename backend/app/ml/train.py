import argparse
import datetime
import logging
import sys
from typing import Dict, Any, Optional
import pandas as pd
from sklearn.model_selection import train_test_split
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.ml.dataset import load_dataset_from_db
from app.ml.features import (
    ALL_FEATURE_COLUMNS,
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES,
    TARGET_COLUMN,
    extract_feature_matrix,
    engineer_features,
)
from app.ml.baseline import BaselineETAModel, DEFAULT_BASELINE_SPEED_KMH
from app.ml.preprocessing import build_model_pipeline
from app.ml.evaluate import calculate_metrics, compare_models
from app.ml.model_registry import (
    save_model,
    extract_feature_importances,
)

logger = logging.getLogger("app.ml.train")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def train_and_evaluate(
    db: Optional[Session] = None,
    model_type: str = "random_forest",
    random_state: int = 42,
    test_size: float = 0.2,
    n_estimators: int = 100,
) -> Dict[str, Any]:
    """
    Execute full end-to-end ML training workflow:
    1. Extract & validate dataset from PostgreSQL / DB.
    2. Engineer temporal and categorical features.
    3. Perform train/test split.
    4. Fit scikit-learn Pipeline (ColumnTransformer + Regressor).
    5. Evaluate baseline and context-aware models on held-out test split.
    6. Compute feature importances.
    7. Persist model and metadata.
    """
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        # Step 1: Load and validate dataset
        raw_df, report = load_dataset_from_db(db)
        if len(raw_df) == 0:
            raise ValueError("No valid records found in database to train model.")

        logger.info(
            "Dataset report: Total=%d, Valid=%d, Invalid=%d",
            report.total_records,
            report.valid_records,
            report.invalid_records,
        )

        # Step 2: Feature engineering
        engineered_df = engineer_features(raw_df)
        X = extract_feature_matrix(engineered_df)
        y = engineered_df[TARGET_COLUMN].values

        # Step 3: Train / Test Split
        # If chronological ordering is available and sufficient samples exist, split chronologically.
        # Otherwise fallback to deterministic shuffle split with explicit note.
        split_method = "chronological"
        total_rows = len(engineered_df)

        if total_rows < 10:
            raise ValueError(f"Dataset too small for reliable train/test evaluation (count: {total_rows}). Minimum 10 rows required.")

        # Check if observation_date allows chronological partitioning
        if "observation_date" in engineered_df.columns and engineered_df["observation_date"].nunique() > 2:
            split_idx = int(total_rows * (1.0 - test_size))
            X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            train_distances = engineered_df["distance_km"].iloc[:split_idx].values
            test_distances = engineered_df["distance_km"].iloc[split_idx:].values
            split_method = "chronological (earlier 80% train -> later 20% test)"
        else:
            X_train, X_test, y_train, y_test, d_train, d_test = train_test_split(
                X, y, engineered_df["distance_km"].values, test_size=test_size, random_state=random_state
            )
            test_distances = d_test
            split_method = "deterministic random_split (reproducible fallback for small/uniform dates)"

        logger.info("Split method: %s | Train rows: %d | Test rows: %d", split_method, len(X_train), len(X_test))

        # Step 4: Baseline Model Evaluation on Test Set
        baseline_model = BaselineETAModel(nominal_speed_kmh=DEFAULT_BASELINE_SPEED_KMH)
        y_pred_baseline = baseline_model.predict(test_distances)
        baseline_metrics = calculate_metrics(y_true=y_test, y_pred=y_pred_baseline)

        # Step 5: Fit Context-Aware ML Model Pipeline
        logger.info("Fitting context-aware %s pipeline...", model_type)
        pipeline = build_model_pipeline(
            model_type=model_type,
            random_state=random_state,
            n_estimators=n_estimators,
        )
        pipeline.fit(X_train, y_train)

        # Step 6: Evaluate Context-Aware Model on Test Set
        y_pred_context = pipeline.predict(X_test)
        context_metrics = calculate_metrics(y_true=y_test, y_pred=y_pred_context)

        # Step 7: Comparison & Feature Importances
        comparison = compare_models(baseline_metrics, context_metrics)
        feature_importances = extract_feature_importances(pipeline, ALL_FEATURE_COLUMNS)

        # Step 8: Build Metadata
        training_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        metadata = {
            "model_name": f"Context-Aware ETA ({model_type.replace('_', ' ').title()})",
            "model_type": model_type,
            "model_version": "1.0.0",
            "training_date": training_timestamp,
            "training_row_count": int(len(X_train)),
            "testing_row_count": int(len(X_test)),
            "total_dataset_rows": int(total_rows),
            "random_state": random_state,
            "split_method": split_method,
            "target_column": TARGET_COLUMN,
            "numerical_features": NUMERICAL_FEATURES,
            "categorical_features": CATEGORICAL_FEATURES,
            "baseline_speed_kmh": DEFAULT_BASELINE_SPEED_KMH,
            "metrics": {
                "baseline": baseline_metrics,
                "context_aware": context_metrics,
                "mae_improvement_pct": comparison["mae_improvement_pct"],
                "rmse_improvement_pct": comparison["rmse_improvement_pct"],
                "is_improved": comparison["is_improved"],
            },
            "feature_importances": feature_importances,
            "dataset_report": report.to_dict(),
            "synthetic_disclaimer": "Synthetic Dataset — Research Prototype. Models are trained on simulated operational data.",
        }

        # Step 9: Save Model and Metadata
        model_path, meta_path = save_model(pipeline, metadata)
        logger.info("Successfully persisted model to %s and metadata to %s", model_path, meta_path)

        # Print clean CLI output
        print("\n" + "=" * 50)
        print("PHASE 3 — ETA MODEL TRAINING COMPLETE")
        print("=" * 50)
        print(f"Dataset rows: {total_rows} (Valid: {report.valid_records}, Invalid: {report.invalid_records})")
        print(f"Training rows: {len(X_train)} | Testing rows: {len(X_test)}")
        print(f"Split Method: {split_method}")
        print("\n--- Baseline Model ---")
        print(f"MAE: {baseline_metrics['mae']} min | RMSE: {baseline_metrics['rmse']} min")
        print(f"Within +/-10min: {baseline_metrics['within_tolerance_pct']}%")
        print("\n--- Context-Aware Random Forest Model ---")
        print(f"MAE: {context_metrics['mae']} min | RMSE: {context_metrics['rmse']} min")
        print(f"Within +/-10min: {context_metrics['within_tolerance_pct']}%")
        print("\n--- Improvement ---")
        print(f"MAE Improvement: {comparison['mae_improvement_pct']}%")
        print(f"RMSE Improvement: {comparison['rmse_improvement_pct']}%")
        print("=" * 50 + "\n")

        return metadata

    finally:
        if close_session:
            db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Smart Waste Context-Aware Travel-Time Model")
    parser.add_argument("--model-type", type=str, default="random_forest", choices=["random_forest", "gradient_boosting"])
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--n-estimators", type=int, default=100)
    args = parser.parse_args()

    train_and_evaluate(
        model_type=args.model_type,
        random_state=args.random_state,
        n_estimators=args.n_estimators,
    )
