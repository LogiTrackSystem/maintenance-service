import os
from typing import List
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import IntervencionMantenimiento
from ..schemas import IntervencionMantenimientoCrear, IntervencionMantenimientoLeer

FLEET_SERVICE_URL = os.getenv("FLEET_SERVICE_URL")

router = APIRouter(prefix="/intervenciones", tags=["Intervenciones de Mantenimiento"])


async def _liberar_vehiculo(vehiculo_id):
    """Cierra el ciclo: registrar una intervención significa que el
    vehículo ya quedó reparado, así que vuelve a estar disponible en Fleet."""
    if not FLEET_SERVICE_URL or not vehiculo_id:
        return
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.patch(
                f"{FLEET_SERVICE_URL}/vehiculos/{vehiculo_id}/estado",
                json={"estado": "active"},
            )
    except Exception as exc:
        print(f"[maintenance] no se pudo liberar el vehículo {vehiculo_id}: {exc}")


@router.post("/", response_model=IntervencionMantenimientoLeer, status_code=201)
async def crear_intervencion(payload: IntervencionMantenimientoCrear, db: Session = Depends(get_db)):
    intervencion = IntervencionMantenimiento(**payload.model_dump())
    db.add(intervencion)
    db.commit()
    db.refresh(intervencion)
    await _liberar_vehiculo(str(intervencion.vehiculo_id))
    return intervencion


@router.get("/{vehiculo_id}", response_model=List[IntervencionMantenimientoLeer])
def listar_intervenciones(vehiculo_id: UUID, db: Session = Depends(get_db)):
    return (
        db.query(IntervencionMantenimiento)
        .filter(IntervencionMantenimiento.vehiculo_id == vehiculo_id)
        .order_by(IntervencionMantenimiento.realizado_en.desc())
        .all()
    )