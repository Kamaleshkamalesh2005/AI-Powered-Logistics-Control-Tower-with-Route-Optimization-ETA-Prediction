from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ShipmentStatus


class ShipmentBase(BaseModel):
    reference: str = Field(min_length=3, max_length=64)
    origin: str = Field(min_length=2, max_length=120)
    destination: str = Field(min_length=2, max_length=120)
    customer_name: str | None = Field(default=None, max_length=160)
    status: ShipmentStatus = ShipmentStatus.CREATED
    eta: datetime | None = None
    planned_pickup_at: datetime | None = None
    planned_delivery_at: datetime | None = None
    actual_delivery_at: datetime | None = None
    notes: str | None = None
    vehicle_id: int | None = None
    driver_id: int | None = None
    trip_id: int | None = None
    created_by_user_id: int | None = None


class ShipmentCreate(ShipmentBase):
    pass


class ShipmentUpdate(BaseModel):
    reference: str | None = Field(default=None, min_length=3, max_length=64)
    origin: str | None = Field(default=None, min_length=2, max_length=120)
    destination: str | None = Field(default=None, min_length=2, max_length=120)
    customer_name: str | None = Field(default=None, max_length=160)
    status: ShipmentStatus | None = None
    eta: datetime | None = None
    planned_pickup_at: datetime | None = None
    planned_delivery_at: datetime | None = None
    actual_delivery_at: datetime | None = None
    notes: str | None = None
    vehicle_id: int | None = None
    driver_id: int | None = None
    trip_id: int | None = None
    created_by_user_id: int | None = None


class ShipmentRead(ShipmentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)