from sqlalchemy import Enum as SAEnum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import VehicleStatus


class Vehicle(TimestampMixin, Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fleet_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    license_plate: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    vin: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    make: Mapped[str | None] = mapped_column(String(80), nullable=True)
    model: Mapped[str | None] = mapped_column(String(80), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    capacity_kg: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    status: Mapped[VehicleStatus] = mapped_column(
        SAEnum(VehicleStatus, name="vehicle_status"),
        nullable=False,
        default=VehicleStatus.AVAILABLE,
        index=True,
    )
    assigned_driver_id: Mapped[int | None] = mapped_column(
        ForeignKey("drivers.id", ondelete="SET NULL"),
        unique=True,
        nullable=True,
    )

    assigned_driver = relationship("Driver", back_populates="assigned_vehicle")
    trips = relationship("Trip", back_populates="vehicle")
    shipments = relationship("Shipment", back_populates="vehicle")