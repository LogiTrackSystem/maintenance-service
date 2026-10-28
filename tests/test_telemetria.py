"""Reglas de mantenimiento preventivo/correctivo al recibir telemetría (sin RabbitMQ ni Fleet reales)."""
import asyncio
import uuid

import pytest

from app import events
from app.models import IntervencionMantenimiento, ProgramaMantenimiento


@pytest.fixture()
def entorno(fabrica, monkeypatch):
    """Sustituye la base, la publicación de eventos y las llamadas a Fleet por dobles de prueba."""
    e = {"eventos": [], "marcados": [], "tipo": "camion"}

    async def publicar(clave, payload):
        e["eventos"].append((clave, payload))

    async def tipo(vehiculo_id):
        return e["tipo"]

    async def marcar(vehiculo_id):
        e["marcados"].append(vehiculo_id)

    monkeypatch.setattr(events, "SessionLocal", fabrica)
    monkeypatch.setattr(events, "publish_event", publicar)
    monkeypatch.setattr(events, "_obtener_tipo_vehiculo", tipo)
    monkeypatch.setattr(events, "_marcar_vehiculo_en_mantenimiento", marcar)
    return e


def procesar(**campos):
    vid = campos.pop("vehiculo_id", None) or str(uuid.uuid4())
    asyncio.run(events._procesar_telemetry_raw({"vehiculo_id": vid, **campos}))
    return vid


def test_camion_alcanza_el_umbral_de_kilometraje(entorno, db):
    vid = procesar(kilometraje_acumulado_km=10000)
    prog = db.query(ProgramaMantenimiento).one()
    assert str(prog.vehiculo_id) == vid and prog.tipo == "preventivo_kilometraje" and prog.prioridad == "alta"
    assert entorno["eventos"][0][0] == "maintenance.alert"
    assert entorno["eventos"][0][1]["motivo"] == "kilometraje"
    assert entorno["marcados"] == []  # la alerta preventiva no retira el vehículo


def test_justo_por_debajo_del_umbral_no_alerta(entorno, db):
    procesar(kilometraje_acumulado_km=9999.9)
    assert db.query(ProgramaMantenimiento).count() == 0 and entorno["eventos"] == []


def test_furgoneta_tiene_un_umbral_menor(entorno, db):
    entorno["tipo"] = "furgoneta"
    procesar(kilometraje_acumulado_km=8000)
    assert db.query(ProgramaMantenimiento).count() == 1


def test_el_kilometraje_se_mide_desde_el_ultimo_servicio(entorno, db):
    vid = uuid.uuid4()
    db.add(IntervencionMantenimiento(vehiculo_id=vid, tipo="general", kilometraje_en_servicio=5000))
    db.commit()
    procesar(vehiculo_id=str(vid), kilometraje_acumulado_km=14000)  # solo 9000 km desde el servicio
    assert entorno["eventos"] == []
    procesar(vehiculo_id=str(vid), kilometraje_acumulado_km=15000)  # 10000 km: toca
    assert len(entorno["eventos"]) == 1


def test_temperatura_alta_es_critica_y_retira_el_vehiculo(entorno, db):
    vid = procesar(temperatura_motor_c=111)
    prog = db.query(ProgramaMantenimiento).one()
    assert prog.tipo == "revision_temperatura_motor" and prog.prioridad == "critica"
    assert entorno["eventos"][0][1]["prioridad"] == "critica"
    assert entorno["marcados"] == [vid]


def test_temperatura_igual_al_umbral_no_alerta(entorno, db):
    procesar(temperatura_motor_c=110)
    assert db.query(ProgramaMantenimiento).count() == 0 and entorno["marcados"] == []


def test_codigo_obd2_genera_diagnostico(entorno, db):
    procesar(codigo_obd2="P0301")
    prog = db.query(ProgramaMantenimiento).one()
    assert prog.tipo == "diagnostico_obd2" and prog.prioridad == "alta"
    assert entorno["eventos"][0][1]["codigo_obd2"] == "P0301"
    assert entorno["marcados"] == []


def test_alertas_repetidas_no_duplican_el_programa(entorno, db):
    vid = procesar(temperatura_motor_c=120)
    procesar(vehiculo_id=vid, temperatura_motor_c=125)
    assert db.query(ProgramaMantenimiento).count() == 1
    assert len(entorno["eventos"]) == 2  # cada lectura anómala sí se notifica


def test_telemetria_normal_no_hace_nada(entorno, db):
    procesar(kilometraje_acumulado_km=100, temperatura_motor_c=80)
    assert db.query(ProgramaMantenimiento).count() == 0 and entorno["eventos"] == []


def test_si_fleet_no_responde_se_usa_el_umbral_por_defecto(entorno, db):
    entorno["tipo"] = None
    procesar(kilometraje_acumulado_km=10000)
    assert db.query(ProgramaMantenimiento).count() == 1
