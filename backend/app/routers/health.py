from fastapi import APIRouter

from app.schemas.health import HealthCheck
from app.services.health import HealthService

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthCheck)
async def read_health() -> HealthCheck:
    return await HealthService.check()