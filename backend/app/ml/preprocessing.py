import logging
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

from app.ml.features import NUMERICAL_FEATURES, CATEGORICAL_FEATURES

logger = logging.getLogger(__name__)


def build_preprocessor() -> ColumnTransformer:
    """
    Construct a scikit-learn ColumnTransformer that:
    - Scales numerical features with StandardScaler
    - Encodes categorical features with OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    """
    numeric_transformer = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            (
                "onehot",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
            )
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, NUMERICAL_FEATURES),
            ("cat", categorical_transformer, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )

    return preprocessor


def build_model_pipeline(
    model_type: str = "random_forest",
    random_state: int = 42,
    n_estimators: int = 100,
    max_depth: int = 12,
) -> Pipeline:
    """
    Construct full ML pipeline with preprocessing and tree-based regressor.
    Supported model types: 'random_forest', 'gradient_boosting'.
    """
    preprocessor = build_preprocessor()

    if model_type == "gradient_boosting":
        regressor = GradientBoostingRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth if max_depth else 5,
            random_state=random_state,
            learning_rate=0.08,
        )
    else:
        regressor = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            n_jobs=-1,
        )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", regressor),
        ]
    )

    return pipeline
