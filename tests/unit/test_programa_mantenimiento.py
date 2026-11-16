"""Unitaria 1: events._crear_o_actualizar_programa crea un programa y luego lo actualiza (sin duplicar)."""
import uuid

from app import events
from app.models import ProgramaMantenimiento


def test_crear_o_actualizar_programa_no_duplica_el_mismo_tipo(db):
    vid = uuid.uuid4()
    events._crear_o_actualizar_programa(db, vid, "diagnostico_obd2", "alta")
    events._crear_o_actualizar_programa(db, vid, "diagnostico_obd2", "critica")
    programa = db.query(ProgramaMantenimiento).one()
    assert programa.prioridad == "critica"
