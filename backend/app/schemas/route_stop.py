from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import RouteStopStatus


class RouteStopBase(BaseModel):
    trip_id: int
    stop_sequence: int = Field(ge=1)
    location_name: str = Field(min_length=2, max_length=160)
    address: str | None = Field(default=None, max_length=255)
    latitude: float | None = None
    longitude: float | None = None
    planned_arrival_at: datetime | None = None
    actual_arrival_at: datetime | None = None
    status: RouteStopStatus = RouteStopStatus.PENDING
    notes: str | None = None


class RouteStopCreate(RouteStopBase):
    pass


class RouteStopUpdate(BaseModel):
    trip_id: int | None = None
    stop_sequence: int | None = Field(default=None, ge=1)
    location_name: str | None = Field(default=None, min_length=2, max_length=160)
    address: str | None = Field(default=None, max_length=255)
    latitude: float | None = None
    longitude: float | None = None
    planned_arrival_at: datetime | None = None
    actual_arrival_at: datetime | None = None
    status: RouteStopStatus | None = None
    notes: str | None = None


class RouteStopRead(RouteStopBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)