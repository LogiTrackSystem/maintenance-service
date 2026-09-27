import uuid
from sqlalchemy import Column, String, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .database import Base


class ProgramaMantenimiento(Base):
    __tablename__ = "programas_mantenimiento"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehiculo_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    tipo = Column(String, nullable=False)
    fecha_vencimiento = Column(DateTime(timezone=True), nullable=True)
    kilometraje_vencimiento = Column(Numeric(10, 2), nullable=True)
    prioridad = Column(String, nullable=False, default="media")
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class IntervencionMantenimiento(Base):
    __tablename__ = "intervenciones_mantenimiento"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehiculo_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    tipo = Column(String, nullable=False)
    realizado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    costo = Column(Numeric(10, 2), nullable=True)
    taller = Column(String, nullable=True)
    kilometraje_en_servicio = Column(Numeric(10, 2), nullable=True)