"""Unitaria 2: events._procesar_telemetry_raw genera alertas cuando la telemetría supera los umbrales."""
import asyncio
import uuid

from app import events
from app.models import ProgramaMantenimiento


def test_temperatura_alta_crea_programa_critico_y_publica_alerta(db, fabrica, monkeypatch):
    # Arrange: dobles para la base, RabbitMQ y Fleet
    publicados = []

    async def publicar(clave, payload):
        publicados.append((clave, payload))

    async def sin_fleet(*args):
        return None

    monkeypatch.setattr(events, "SessionLocal", fabrica)
    monkeypatch.setattr(events, "publish_event", publicar)
    monkeypatch.setattr(events, "_obtener_tipo_vehiculo", sin_fleet)
    monkeypatch.setattr(events, "_marcar_vehiculo_en_mantenimiento", sin_fleet)
    # Act
    asyncio.run(events._procesar_telemetry_raw({"vehiculo_id": str(uuid.uuid4()), "temperatura_motor_c": 120}))
    # Assert
    assert db.query(ProgramaMantenimiento).one().prioridad == "critica"
    assert publicados[0][0] == "maintenance.alert" and publicados[0][1]["motivo"] == "temperatura_motor"
