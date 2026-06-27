from datetime import datetime, timezone

from app.schemas.health import HealthCheck


class HealthService:
    @staticmethod
    async def check() -> HealthCheck:
        return HealthCheck(
            status="ok",
            service="ai-logistics-control-tower",
            timestamp=datetime.now(timezone.utc),
        )