from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.analytics import DelayAnalyticsRequest, DelayAnalyticsResponse
from app.services.analytics import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post(
    "/delays",
    response_model=DelayAnalyticsResponse,
    summary="Aggregate delay analytics",
    description="Returns route, vehicle, and time-period delay analytics with Redis caching, anomaly detection, and cause breakdowns for charting.",
)
async def get_delay_analytics(payload: DelayAnalyticsRequest, db: AsyncSession = Depends(get_db)) -> DelayAnalyticsResponse:
    service = AnalyticsService(db)
    return await service.get_delay_analytics(payload)
