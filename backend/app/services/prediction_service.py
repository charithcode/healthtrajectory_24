"""Reusable prediction service for the HealthTrajectory MVP.

This project does not have a repository-backed labeled dataset, so the service uses an
explicit DEMO MODE that is honest about not being clinically validated. A real trained
XGBoost model can be plugged in via the same interface when available.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import shap
import xgboost as xgb

from app.schemas.features import (
    FeatureMeasurement,
    InfluentialFeature,
    PredictionResponse,
)
from app.services.feature_dictionary import (
    BASIC_REQUIRED_FEATURES,
    validate_basic_features,
)

MODEL_PATH = Path(__file__).resolve().parents[3] / "models" / "artifacts" / "demo_xgboost_model.json"
FEATURE_ORDER = [
    "age",
    "sex",
    "bmi",
    "fasting_glucose",
    "hba1c",
    "total_cholesterol",
    "hdl",
    "ldl",
    "triglycerides",
    "creatinine",
]


class PredictionService:
    def __init__(self, model_path: str | Path = MODEL_PATH):
        self.model_path = Path(model_path)
        self.model = self._load_model()
        self.model_status = "model" if self.model is not None else "demo"

    def _load_model(self) -> xgb.Booster | None:
        if not self.model_path.exists():
            return None

        try:
            return xgb.Booster()
        except (OSError, TypeError, ValueError):
            return None

    def _prepare_features(self, measurements: list[FeatureMeasurement]) -> dict[str, Any]:
        feature_values: dict[str, Any] = {}
        for measurement in measurements:
            if measurement.name in {"sex", "gender"}:
                feature_values["sex"] = str(measurement.value).lower()
            elif measurement.name == "age":
                feature_values["age"] = float(measurement.value)
            elif measurement.name == "bmi":
                feature_values["bmi"] = float(measurement.value)
            elif measurement.name in {"fbs", "fasting glucose", "fasting_glucose"}:
                feature_values["fasting_glucose"] = float(measurement.value)
            elif measurement.name in {"hba1c", "hb a1c", "glycated hemoglobin"}:
                feature_values["hba1c"] = float(measurement.value)
            elif measurement.name in {"total cholesterol", "cholesterol"}:
                feature_values["total_cholesterol"] = float(measurement.value)
            elif measurement.name in {"hdl", "hdl cholesterol"}:
                feature_values["hdl"] = float(measurement.value)
            elif measurement.name in {"ldl", "ldl cholesterol"}:
                feature_values["ldl"] = float(measurement.value)
            elif measurement.name in {"triglycerides", "tg"}:
                feature_values["triglycerides"] = float(measurement.value)
            elif measurement.name in {"creatinine", "serum creatinine"}:
                feature_values["creatinine"] = float(measurement.value)

        return feature_values

    def _to_feature_row(self, feature_values: dict[str, Any]) -> pd.DataFrame:
        row: dict[str, Any] = {feature: 0.0 for feature in FEATURE_ORDER}
        row["sex"] = 1 if feature_values.get("sex", "female") == "female" else 0
        for feature in FEATURE_ORDER:
            if feature in {"sex"}:
                continue
            if feature in feature_values:
                row[feature] = float(feature_values[feature])
        return pd.DataFrame([row], columns=FEATURE_ORDER)

    def risk_level_for_probability(self, probability: float | Decimal) -> str:
        value = float(probability)
        if value < 0.33:
            return "LOW"
        if value < 0.66:
            return "MODERATE"
        return "HIGH"

    def _safe_shap(self, model: xgb.Booster | None, features: pd.DataFrame) -> list[InfluentialFeature]:
        if model is None:
            return []

        try:
            explainer = shap.TreeExplainer(model)
            values = explainer.shap_values(features)
            if isinstance(values, list):
                values = values[1]
            if hasattr(values, "shape") and len(values.shape) > 1:
                row_values = values[0]
            else:
                row_values = np.asarray(values)

            ranking = sorted(
                zip(features.columns.tolist(), np.abs(np.asarray(row_values)).tolist()),
                key=lambda item: item[1],
                reverse=True,
            )[:5]

            influential: list[InfluentialFeature] = []
            for feature_name, importance in ranking:
                if feature_name == "sex":
                    direction = "increases_risk" if float(row_values[features.columns.get_loc(feature_name)]) >= 0 else "decreases_risk"
                else:
                    direction = "increases_risk" if float(row_values[features.columns.get_loc(feature_name)]) >= 0 else "decreases_risk"
                influential.append(
                    InfluentialFeature(
                        feature=feature_name,
                        importance=max(0.0, min(1.0, float(importance))),
                        direction=direction,
                    )
                )
            return influential
        except (AttributeError, TypeError, ValueError):
            return []

    def predict(self, measurements: list[FeatureMeasurement]) -> PredictionResponse:
        validation = validate_basic_features(measurements)
        if not validation.eligible_for_basic_model:
            return PredictionResponse(
                prediction_available=False,
                prediction_status="unavailable",
                risk_probability=None,
                risk_level=None,
                model_version=None,
                features_used=validation.available_features,
                influential_features=[],
                missing_required_features=validation.missing_required_features,
                warnings=[
                    "Assessment unavailable. More information is required.",
                    *(
                        [f"Missing required features: {', '.join(validation.missing_required_features)}"]
                        if validation.missing_required_features
                        else []
                    ),
                ],
                disclaimer="This is a research decision-support prototype. It is not a diagnosis and does not replace professional medical evaluation.",
            )

        feature_values = self._prepare_features(measurements)
        features_df = self._to_feature_row(feature_values)
        model = self.model

        if model is None:
            risk_probability = 0.5
            return PredictionResponse(
                prediction_available=True,
                prediction_status="demo",
                risk_probability=risk_probability,
                risk_level=self.risk_level_for_probability(risk_probability),
                model_version="demo-v0",
                features_used=[feature for feature in BASIC_REQUIRED_FEATURES if feature in feature_values or feature == "sex"],
                influential_features=[],
                missing_required_features=[],
                warnings=[
                    "Demo mode is active: a real trained XGBoost model is not available in this repository.",
                    "SHAP explanation is unavailable because no real model artifact is present in this repository.",
                    "This result is for research-only demonstration and is not clinically validated.",
                ],
                disclaimer="This is a research decision-support prototype. It is not a diagnosis and does not replace professional medical evaluation.",
            )

        prediction = float(model.predict(xgb.DMatrix(features_df))[0])
        probability = min(1.0, max(0.0, prediction))
        result = PredictionResponse(
            prediction_available=True,
            prediction_status="model",
            risk_probability=probability,
            risk_level=self.risk_level_for_probability(probability),
            model_version="xgboost-demo",
            features_used=[feature for feature in FEATURE_ORDER if feature in feature_values],
            influential_features=self._safe_shap(model, features_df),
            missing_required_features=[],
            warnings=[],
            disclaimer="This is a research decision-support prototype. It is not a diagnosis and does not replace professional medical evaluation.",
        )
        return result
