from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DelaySeverity


class DelayEventBase(BaseModel):
    trip_id: int
    shipment_id: int | None = None
    route_stop_id: int | None = None
    reported_by_user_id: int | None = None
    severity: DelaySeverity = DelaySeverity.MEDIUM
    delay_minutes: int = Field(ge=0)
    reason_code: str | None = Field(default=None, max_length=64)
    description: str | None = None
    occurred_at: datetime
    resolved_at: datetime | None = None


class DelayEventCreate(DelayEventBase):
    pass


class DelayEventUpdate(BaseModel):
    trip_id: int | None = None
    shipment_id: int | None = None
    route_stop_id: int | None = None
    reported_by_user_id: int | None = None
    severity: DelaySeverity | None = None
    delay_minutes: int | None = Field(default=None, ge=0)
    reason_code: str | None = Field(default=None, max_length=64)
    description: str | None = None
    occurred_at: datetime | None = None
    resolved_at: datetime | None = None


class DelayEventRead(DelayEventBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)