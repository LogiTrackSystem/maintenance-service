"""Programas e intervenciones de mantenimiento (API)."""
import uuid

from app.routers import intervenciones


def test_crear_y_listar_programas_de_un_vehiculo(api):
    vid = str(uuid.uuid4())
    r = api.post("/programas/", json={"vehiculo_id": vid, "tipo": "cambio_aceite", "prioridad": "alta"})
    assert r.status_code == 201
    assert r.json()["vehiculo_id"] == vid and r.json()["prioridad"] == "alta"
    lista = api.get(f"/programas/{vid}").json()
    assert [p["tipo"] for p in lista] == ["cambio_aceite"]


def test_los_programas_son_por_vehiculo(api):
    a, b = str(uuid.uuid4()), str(uuid.uuid4())
    api.post("/programas/", json={"vehiculo_id": a, "tipo": "frenos"})
    assert api.get(f"/programas/{b}").json() == []


def test_programa_con_prioridad_por_defecto_media(api):
    vid = str(uuid.uuid4())
    r = api.post("/programas/", json={"vehiculo_id": vid, "tipo": "llantas"})
    assert r.json()["prioridad"] == "media"


def test_programa_con_vehiculo_invalido_da_422(api):
    assert api.post("/programas/", json={"vehiculo_id": "no-es-uuid", "tipo": "x"}).status_code == 422
    assert api.get("/programas/no-es-uuid").status_code == 422


def test_programa_sin_tipo_da_422(api):
    assert api.post("/programas/", json={"vehiculo_id": str(uuid.uuid4())}).status_code == 422


def test_registrar_intervencion_libera_el_vehiculo_en_fleet(api, monkeypatch):
    liberados = []

    async def falso(vehiculo_id):
        liberados.append(vehiculo_id)

    monkeypatch.setattr(intervenciones, "_liberar_vehiculo", falso)
    vid = str(uuid.uuid4())
    r = api.post("/intervenciones/", json={"vehiculo_id": vid, "tipo": "motor", "costo": "150000.50", "taller": "Taller Sur"})
    assert r.status_code == 201
    assert r.json()["taller"] == "Taller Sur"
    assert liberados == [vid]


def test_listar_intervenciones_de_la_mas_reciente_a_la_mas_antigua(api, db, monkeypatch):
    from datetime import datetime, timedelta, timezone

    from app.models import IntervencionMantenimiento

    async def falso(vehiculo_id):
        return None

    monkeypatch.setattr(intervenciones, "_liberar_vehiculo", falso)
    vid = uuid.uuid4()
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for i, tipo in enumerate(["vieja", "media", "nueva"]):
        db.add(IntervencionMantenimiento(vehiculo_id=vid, tipo=tipo, realizado_en=base + timedelta(days=i)))
    db.commit()
    assert [x["tipo"] for x in api.get(f"/intervenciones/{vid}").json()] == ["nueva", "media", "vieja"]


def test_liberar_vehiculo_sin_fleet_configurado_no_hace_nada(monkeypatch):
    import asyncio

    monkeypatch.setattr(intervenciones, "FLEET_SERVICE_URL", None)
    assert asyncio.run(intervenciones._liberar_vehiculo(str(uuid.uuid4()))) is None
