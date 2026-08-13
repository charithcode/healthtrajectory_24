"""XGBoost training entry point for the HealthTrajectory MVP.

This repository does not include a verified labeled dataset, so this module intentionally
runs in DEMO MODE and refuses to fabricate clinical labels or metrics. When a real,
well-scoped dataset is available, the same interface can be used to train an actual model.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

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


@dataclass
class TrainingMetadata:
    model_version: str
    dataset: str
    target: str
    feature_list: list[str]
    training_date_utc: str
    metrics: dict[str, float | str | None]
    status: str


def _expected_dataset_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "processed"


def prepare_training_plan(dataset_path: str | Path | None = None) -> TrainingMetadata:
    """Return the honest training plan when no real labeled dataset is present."""
    resolved = Path(dataset_path) if dataset_path is not None else _expected_dataset_path()
    if not resolved.exists() or not any(resolved.iterdir()):
        return TrainingMetadata(
            model_version="demo-mode",
            dataset="not-available",
            target="not-available",
            feature_list=FEATURE_ORDER,
            training_date_utc=datetime.now(timezone.utc).isoformat(),
            metrics={
                "status": "demo_mode",
                "precision": None,
                "recall": None,
                "f1": None,
                "roc_auc": None,
                "message": "No real labeled dataset was found in the repository. Training is intentionally skipped.",
            },
            status="demo",
        )

    return TrainingMetadata(
        model_version="pending-real-training",
        dataset=str(resolved),
        target="requires-actual-dataset-target",
        feature_list=FEATURE_ORDER,
        training_date_utc=datetime.now(timezone.utc).isoformat(),
        metrics={
            "status": "dataset-present",
            "precision": None,
            "recall": None,
            "f1": None,
            "roc_auc": None,
            "message": "A real dataset is present, but the target and model training must still be defined from the source data.",
        },
        status="ready-for-real-training",
    )


def main() -> None:
    metadata = prepare_training_plan()
    print("HealthTrajectory XGBoost training status:", metadata.status)
    print("Model version:", metadata.model_version)
    print("Dataset:", metadata.dataset)
    print("Target:", metadata.target)
    print("Feature list:", metadata.feature_list)
    if metadata.status == "demo":
        print("Demo mode is active because no labeled dataset is committed in this repository.")


if __name__ == "__main__":
    main()
