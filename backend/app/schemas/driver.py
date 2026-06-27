from datetime import date
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import DriverStatus


class DriverBase(BaseModel):
    employee_code: str = Field(min_length=2, max_length=64)
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    email: EmailStr | None = None
    phone_number: str | None = Field(default=None, max_length=40)
    license_number: str = Field(min_length=3, max_length=64)
    license_expiry: date | None = None
    home_base: str | None = Field(default=None, max_length=120)
    status: DriverStatus = DriverStatus.ACTIVE
    user_id: int | None = None


class DriverCreate(DriverBase):
    pass


class DriverUpdate(BaseModel):
    employee_code: str | None = Field(default=None, min_length=2, max_length=64)
    first_name: str | None = Field(default=None, min_length=1, max_length=80)
    last_name: str | None = Field(default=None, min_length=1, max_length=80)
    email: EmailStr | None = None
    phone_number: str | None = Field(default=None, max_length=40)
    license_number: str | None = Field(default=None, min_length=3, max_length=64)
    license_expiry: date | None = None
    home_base: str | None = Field(default=None, max_length=120)
    status: DriverStatus | None = None
    user_id: int | None = None


class DriverRead(DriverBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)