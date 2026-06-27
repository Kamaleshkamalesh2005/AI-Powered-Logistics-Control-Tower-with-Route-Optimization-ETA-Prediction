from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.shipment import ShipmentCreate, ShipmentRead, ShipmentUpdate
from app.services.shipment import ShipmentService

router = APIRouter(prefix="/shipments", tags=["shipments"])


@router.get("", response_model=list[ShipmentRead])
async def list_shipments(db: AsyncSession = Depends(get_db)) -> list[ShipmentRead]:
    service = ShipmentService(db)
    return await service.list_shipments()


@router.get("/{shipment_id}", response_model=ShipmentRead)
async def read_shipment(shipment_id: int, db: AsyncSession = Depends(get_db)) -> ShipmentRead:
    service = ShipmentService(db)
    shipment = await service.get_shipment(shipment_id)
    if shipment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
    return shipment


@router.post("", response_model=ShipmentRead, status_code=status.HTTP_201_CREATED)
async def create_shipment(payload: ShipmentCreate, db: AsyncSession = Depends(get_db)) -> ShipmentRead:
    service = ShipmentService(db)
    return await service.create_shipment(payload)


@router.put("/{shipment_id}", response_model=ShipmentRead)
async def update_shipment(
    shipment_id: int,
    payload: ShipmentUpdate,
    db: AsyncSession = Depends(get_db),
) -> ShipmentRead:
    service = ShipmentService(db)
    shipment = await service.get_shipment(shipment_id)
    if shipment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
    return await service.update_shipment(shipment, payload)