"""Integración: programa y intervención creados por API se consultan por vehículo."""
import uuid

from app.routers import intervenciones


def test_programa_e_intervencion_se_registran_y_consultan_por_vehiculo(api, monkeypatch):
    # Arrange: Fleet (simulado) no se llama de verdad
    async def sin_fleet(vehiculo_id):
        return None

    monkeypatch.setattr(intervenciones, "_liberar_vehiculo", sin_fleet)
    vid = str(uuid.uuid4())
    # Act
    programa = api.post("/programas/", json={"vehiculo_id": vid, "tipo": "cambio_aceite", "prioridad": "alta"})
    intervencion = api.post("/intervenciones/", json={"vehiculo_id": vid, "tipo": "cambio_aceite", "taller": "Taller Sur"})
    # Assert
    assert programa.status_code == 201 and intervencion.status_code == 201
    assert api.get(f"/programas/{vid}").json()[0]["tipo"] == "cambio_aceite"
    assert api.get(f"/intervenciones/{vid}").json()[0]["taller"] == "Taller Sur"
