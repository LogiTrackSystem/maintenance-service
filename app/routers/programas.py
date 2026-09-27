from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ProgramaMantenimiento
from ..schemas import ProgramaMantenimientoCrear, ProgramaMantenimientoLeer

router = APIRouter(prefix="/programas", tags=["Programas de Mantenimiento"])


@router.post("/", response_model=ProgramaMantenimientoLeer, status_code=201)
def crear_programa(payload: ProgramaMantenimientoCrear, db: Session = Depends(get_db)):
    programa = ProgramaMantenimiento(**payload.model_dump())
    db.add(programa)
    db.commit()
    db.refresh(programa)
    return programa


@router.get("/{vehiculo_id}", response_model=List[ProgramaMantenimientoLeer])
def listar_programas(vehiculo_id: UUID, db: Session = Depends(get_db)):
    return (
        db.query(ProgramaMantenimiento)
        .filter(ProgramaMantenimiento.vehiculo_id == vehiculo_id)
        .all()
    )