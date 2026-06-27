from fastapi import APIRouter

from app.schemas.eta_prediction import EtaPredictionRequest, EtaPredictionResponse
from app.services.eta_prediction import EtaPredictionService

router = APIRouter(prefix="", tags=["eta-prediction"])


@router.post(
    "/predict-eta",
    response_model=EtaPredictionResponse,
    summary="Predict shipment ETA in minutes",
    description="Uses a trained XGBoost regression model with validated categorical and numeric features to estimate shipment ETA.",
)
async def predict_eta(payload: EtaPredictionRequest) -> EtaPredictionResponse:
    service = EtaPredictionService()
    return service.predict(payload)