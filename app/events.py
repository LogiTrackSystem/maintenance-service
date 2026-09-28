import json
import os
import uuid
import aio_pika
import httpx
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import ProgramaMantenimiento, IntervencionMantenimiento

RABBITMQ_URL = os.getenv("RABBITMQ_URL")
FLEET_SERVICE_URL = os.getenv("FLEET_SERVICE_URL")
EXCHANGE_NAME = "logitrack_events"

UMBRAL_KM_POR_TIPO = {
    "camion": 10000,
    "furgoneta": 8000,
    "van": 8000,
}
UMBRAL_KM_DEFECTO = 10000
UMBRAL_TEMPERATURA_MOTOR_C = 110


async def publish_event(routing_key: str, payload: dict):
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
        )
        message = aio_pika.Message(
            body=json.dumps(payload, default=str).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await exchange.publish(message, routing_key=routing_key)


async def _obtener_tipo_vehiculo(vehiculo_id: str):
    if not FLEET_SERVICE_URL:
        return None
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{FLEET_SERVICE_URL}/vehiculos/{vehiculo_id}")
            resp.raise_for_status()
            return resp.json().get("tipo")
    except Exception:
        return None


async def _marcar_vehiculo_en_mantenimiento(vehiculo_id: str):
    """Cierra el hueco de 'vehiculos.estado nunca cambia': ante una alerta
    crítica (no las preventivas por kilometraje/OBD2, esas son solo aviso
    de programar servicio), el vehículo se retira de servicio en Fleet."""
    if not FLEET_SERVICE_URL or not vehiculo_id:
        return
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.patch(
                f"{FLEET_SERVICE_URL}/vehiculos/{vehiculo_id}/estado",
                json={"estado": "en_mantenimiento"},
            )
    except Exception as exc:
        print(f"[maintenance] no se pudo marcar el vehículo {vehiculo_id} en_mantenimiento: {exc}")


def _ultimo_kilometraje_servicio(db: Session, vehiculo_id):
    ultima = (
        db.query(IntervencionMantenimiento)
        .filter(IntervencionMantenimiento.vehiculo_id == vehiculo_id)
        .order_by(IntervencionMantenimiento.realizado_en.desc())
        .first()
    )
    if ultima and ultima.kilometraje_en_servicio is not None:
        return float(ultima.kilometraje_en_servicio)
    return 0.0


def _crear_o_actualizar_programa(db: Session, vehiculo_id, tipo, prioridad, kilometraje_vencimiento=None):
    programa = (
        db.query(ProgramaMantenimiento)
        .filter(
            ProgramaMantenimiento.vehiculo_id == vehiculo_id,
            ProgramaMantenimiento.tipo == tipo,
        )
        .first()
    )
    if programa:
        programa.prioridad = prioridad
        if kilometraje_vencimiento is not None:
            programa.kilometraje_vencimiento = kilometraje_vencimiento
    else:
        programa = ProgramaMantenimiento(
            vehiculo_id=vehiculo_id,
            tipo=tipo,
            prioridad=prioridad,
            kilometraje_vencimiento=kilometraje_vencimiento,
        )
        db.add(programa)
    db.commit()
    return programa


async def _procesar_telemetry_raw(payload: dict):
    vehiculo_id = uuid.UUID(payload["vehiculo_id"])
    kilometraje = payload.get("kilometraje_acumulado_km")
    temperatura_motor = payload.get("temperatura_motor_c")
    codigo_obd2 = payload.get("codigo_obd2")

    db: Session = SessionLocal()
    try:
        tipo_vehiculo = await _obtener_tipo_vehiculo(str(vehiculo_id))
        umbral_km = UMBRAL_KM_POR_TIPO.get(tipo_vehiculo, UMBRAL_KM_DEFECTO)

        if kilometraje is not None:
            kilometraje = float(kilometraje)
            ultimo_km = _ultimo_kilometraje_servicio(db, vehiculo_id)
            if kilometraje - ultimo_km >= umbral_km:
                _crear_o_actualizar_programa(
                    db, vehiculo_id, "preventivo_kilometraje", "alta",
                    kilometraje_vencimiento=kilometraje,
                )
                await publish_event("maintenance.alert", {
                    "vehiculo_id": str(vehiculo_id),
                    "motivo": "kilometraje",
                    "kilometraje_acumulado_km": kilometraje,
                    "prioridad": "alta",
                })

        if temperatura_motor is not None and float(temperatura_motor) > UMBRAL_TEMPERATURA_MOTOR_C:
            _crear_o_actualizar_programa(db, vehiculo_id, "revision_temperatura_motor", "critica")
            await publish_event("maintenance.alert", {
                "vehiculo_id": str(vehiculo_id),
                "motivo": "temperatura_motor",
                "temperatura_motor_c": float(temperatura_motor),
                "prioridad": "critica",
            })
            await _marcar_vehiculo_en_mantenimiento(str(vehiculo_id))

        if codigo_obd2:
            _crear_o_actualizar_programa(db, vehiculo_id, "diagnostico_obd2", "alta")
            await publish_event("maintenance.alert", {
                "vehiculo_id": str(vehiculo_id),
                "motivo": "codigo_obd2",
                "codigo_obd2": codigo_obd2,
                "prioridad": "alta",
            })
    finally:
        db.close()


async def _on_message(message: aio_pika.IncomingMessage):
    async with message.process():
        payload = json.loads(message.body.decode())
        await _procesar_telemetry_raw(payload)


async def iniciar_consumidor():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    exchange = await channel.declare_exchange(
        EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
    )
    queue = await channel.declare_queue("maintenance_service.telemetry_raw", durable=True)
    await queue.bind(exchange, routing_key="telemetry.raw")
    await queue.consume(_on_message)
    return connection