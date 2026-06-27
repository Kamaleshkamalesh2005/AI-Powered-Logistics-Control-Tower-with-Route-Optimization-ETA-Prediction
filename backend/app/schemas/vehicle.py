from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import VehicleStatus


class VehicleBase(BaseModel):
    fleet_number: str = Field(min_length=2, max_length=64)
    license_plate: str = Field(min_length=2, max_length=32)
    vin: str | None = Field(default=None, max_length=64)
    make: str | None = Field(default=None, max_length=80)
    model: str | None = Field(default=None, max_length=80)
    year: int | None = Field(default=None, ge=1900, le=2100)
    capacity_kg: float | None = Field(default=None, gt=0)
    status: VehicleStatus = VehicleStatus.AVAILABLE
    assigned_driver_id: int | None = None


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    fleet_number: str | None = Field(default=None, min_length=2, max_length=64)
    license_plate: str | None = Field(default=None, min_length=2, max_length=32)
    vin: str | None = Field(default=None, max_length=64)
    make: str | None = Field(default=None, max_length=80)
    model: str | None = Field(default=None, max_length=80)
    year: int | None = Field(default=None, ge=1900, le=2100)
    capacity_kg: float | None = Field(default=None, gt=0)
    status: VehicleStatus | None = None
    assigned_driver_id: int | None = None


class VehicleRead(VehicleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)