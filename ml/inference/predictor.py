"""Reusable XGBoost prediction interface for the HealthTrajectory MVP.

This module is intentionally honest: if no real trained artifact is available, it does
not fabricate a clinical prediction or SHAP output. The backend prediction service owns
that decision path and surfaces DEMO MODE explicitly.
"""

from __future__ import annotations

from pathlib import Path

import xgboost as xgb

DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "artifacts" / "xgboost_model.json"


def load_model(model_path: str | Path | None = None) -> xgb.Booster | None:
    path = Path(model_path) if model_path is not None else DEFAULT_MODEL_PATH
    if not path.exists():
        return None

    try:
        booster = xgb.Booster()
        booster.load_model(str(path))
        return booster
    except (OSError, ValueError, TypeError):
        return None


def model_available(model_path: str | Path | None = None) -> bool:
    return load_model(model_path) is not None
