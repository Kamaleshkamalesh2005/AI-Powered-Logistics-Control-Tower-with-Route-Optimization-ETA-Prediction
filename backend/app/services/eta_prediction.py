from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from time import perf_counter
from typing import Any

import joblib
import pandas as pd
from fastapi import HTTPException, status

from app.core.config import settings
from app.schemas.eta_prediction import EtaPredictionRequest, EtaPredictionResponse

BACKEND_ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def load_eta_artifact() -> dict[str, Any]:
    artifact_path = Path(settings.eta_model_path)
    if not artifact_path.is_absolute():
        artifact_path = BACKEND_ROOT / artifact_path

    if not artifact_path.exists():
        raise FileNotFoundError(f"ETA model artifact not found at {artifact_path}")

    artifact = joblib.load(artifact_path)
    if not isinstance(artifact, dict) or "model" not in artifact:
        raise RuntimeError("ETA model artifact is malformed")
    return artifact


def warm_eta_model_cache() -> None:
    try:
        load_eta_artifact()
    except FileNotFoundError:
        return


class EtaPredictionService:
    def predict(self, payload: EtaPredictionRequest) -> EtaPredictionResponse:
        start = perf_counter()

        try:
            artifact = load_eta_artifact()
        except FileNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ETA model is not trained yet. Run the training script to generate the joblib artifact.",
            ) from exc

        model = artifact["model"]
        features = pd.DataFrame([payload.model_dump()])
        prediction = float(model.predict(features)[0])
        inference_ms = round((perf_counter() - start) * 1000.0, 3)

        return EtaPredictionResponse(
            predicted_eta_minutes=round(max(prediction, 0.0), 2),
            model_version=str(artifact.get("trained_at", "unknown")),
            inference_ms=inference_ms,
        )