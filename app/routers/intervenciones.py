from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import IntervencionMantenimiento
from ..schemas import IntervencionMantenimientoCrear, IntervencionMantenimientoLeer

router = APIRouter(prefix="/intervenciones", tags=["Intervenciones de Mantenimiento"])


@router.post("/", response_model=IntervencionMantenimientoLeer, status_code=201)
def crear_intervencion(payload: IntervencionMantenimientoCrear, db: Session = Depends(get_db)):
    intervencion = IntervencionMantenimiento(**payload.model_dump())
    db.add(intervencion)
    db.commit()
    db.refresh(intervencion)
    return intervencion


@router.get("/{vehiculo_id}", response_model=List[IntervencionMantenimientoLeer])
def listar_intervenciones(vehiculo_id: UUID, db: Session = Depends(get_db)):
    return (
        db.query(IntervencionMantenimiento)
        .filter(IntervencionMantenimiento.vehiculo_id == vehiculo_id)
        .order_by(IntervencionMantenimiento.realizado_en.desc())
        .all()
    )