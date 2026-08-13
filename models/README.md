# Model artifacts

This repository intentionally does not ship a real trained XGBoost model because no verified labeled dataset is committed here.

Current state:
- DEMO MODE is active in the backend prediction service.
- A real XGBoost artifact can be added later at `models/artifacts/xgboost_model.json`.
- The training pipeline in `ml/training/xgboost_training.py` is set up to support a real dataset when one is available.

Do not claim clinical validation or fabricated model performance metrics.
