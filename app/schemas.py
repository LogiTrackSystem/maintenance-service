import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ProgramaMantenimientoCrear(BaseModel):
    vehiculo_id: uuid.UUID
    tipo: str
    fecha_vencimiento: Optional[datetime] = None
    kilometraje_vencimiento: Optional[Decimal] = None
    prioridad: str = "media"


class ProgramaMantenimientoLeer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    vehiculo_id: uuid.UUID
    tipo: str
    fecha_vencimiento: Optional[datetime] = None
    kilometraje_vencimiento: Optional[Decimal] = None
    prioridad: str
    creado_en: datetime
    actualizado_en: datetime


class IntervencionMantenimientoCrear(BaseModel):
    vehiculo_id: uuid.UUID
    tipo: str
    costo: Optional[Decimal] = None
    taller: Optional[str] = None
    kilometraje_en_servicio: Optional[Decimal] = None


class IntervencionMantenimientoLeer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    vehiculo_id: uuid.UUID
    tipo: str
    realizado_en: datetime
    costo: Optional[Decimal] = None
    taller: Optional[str] = None
    kilometraje_en_servicio: Optional[Decimal] = None