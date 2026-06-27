from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import DelaySeverity


class DelayEvent(TimestampMixin, Base):
    __tablename__ = "delay_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    shipment_id: Mapped[int | None] = mapped_column(ForeignKey("shipments.id", ondelete="SET NULL"), nullable=True)
    route_stop_id: Mapped[int | None] = mapped_column(ForeignKey("route_stops.id", ondelete="SET NULL"), nullable=True)
    reported_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    severity: Mapped[DelaySeverity] = mapped_column(
        SAEnum(DelaySeverity, name="delay_severity"),
        nullable=False,
        default=DelaySeverity.MEDIUM,
        index=True,
    )
    delay_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    reason_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    trip = relationship("Trip", back_populates="delay_events")
    shipment = relationship("Shipment", back_populates="delay_events")
    route_stop = relationship("RouteStop", back_populates="delay_events")