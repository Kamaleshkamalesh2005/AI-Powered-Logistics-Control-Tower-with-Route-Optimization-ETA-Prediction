from datetime import date

from sqlalchemy import Date, Enum as SAEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import DriverStatus


class Driver(TimestampMixin, Base):
    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(40), nullable=True)
    license_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    license_expiry: Mapped[date | None] = mapped_column(Date, nullable=True)
    home_base: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[DriverStatus] = mapped_column(
        SAEnum(DriverStatus, name="driver_status"),
        nullable=False,
        default=DriverStatus.ACTIVE,
        index=True,
    )
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), unique=True, nullable=True)

    user = relationship("User", back_populates="driver_profile")
    assigned_vehicle = relationship("Vehicle", back_populates="assigned_driver", uselist=False)
    trips = relationship("Trip", back_populates="driver")
    shipments = relationship("Shipment", back_populates="driver")