from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shipment import Shipment
from app.schemas.shipment import ShipmentCreate, ShipmentUpdate


class ShipmentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_shipments(self) -> list[Shipment]:
        result = await self.session.execute(select(Shipment).order_by(Shipment.id.desc()))
        return list(result.scalars().all())

    async def get_shipment(self, shipment_id: int) -> Shipment | None:
        return await self.session.get(Shipment, shipment_id)

    async def create_shipment(self, payload: ShipmentCreate) -> Shipment:
        shipment = Shipment(
            reference=payload.reference,
            origin=payload.origin,
            destination=payload.destination,
            status=payload.status,
            eta=payload.eta,
        )
        self.session.add(shipment)
        await self.session.commit()
        await self.session.refresh(shipment)
        return shipment

    async def update_shipment(self, shipment: Shipment, payload: ShipmentUpdate) -> Shipment:
        update_data = payload.model_dump(exclude_unset=True)
        for field_name, value in update_data.items():
            setattr(shipment, field_name, value)

        await self.session.commit()
        await self.session.refresh(shipment)
        return shipment