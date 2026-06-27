from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TripStatus


class TripBase(BaseModel):
    trip_number: str = Field(min_length=2, max_length=64)
    route_name: str | None = Field(default=None, max_length=160)
    status: TripStatus = TripStatus.PLANNED
    planned_departure_at: datetime | None = None
    planned_arrival_at: datetime | None = None
    actual_departure_at: datetime | None = None
    actual_arrival_at: datetime | None = None
    notes: str | None = None
    vehicle_id: int | None = None
    driver_id: int | None = None
    created_by_user_id: int | None = None


class TripCreate(TripBase):
    pass


class TripUpdate(BaseModel):
    trip_number: str | None = Field(default=None, min_length=2, max_length=64)
    route_name: str | None = Field(default=None, max_length=160)
    status: TripStatus | None = None
    planned_departure_at: datetime | None = None
    planned_arrival_at: datetime | None = None
    actual_departure_at: datetime | None = None
    actual_arrival_at: datetime | None = None
    notes: str | None = None
    vehicle_id: int | None = None
    driver_id: int | None = None
    created_by_user_id: int | None = None


class TripRead(TripBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)