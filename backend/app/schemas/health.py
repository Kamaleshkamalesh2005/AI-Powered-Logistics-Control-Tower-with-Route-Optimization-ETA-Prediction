from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HealthCheck(BaseModel):
    status: str
    service: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)