"""Pruebas de Maintenance con SQLite en memoria (sin PostgreSQL, RabbitMQ ni Fleet)."""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite://"
os.environ.pop("INTERNAL_API_KEY", None)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def fabrica():
    """Fábrica de sesiones sobre una misma base SQLite en memoria."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, autoflush=False)
    engine.dispose()


@pytest.fixture()
def db(fabrica):
    sesion = fabrica()
    yield sesion
    sesion.close()


@pytest.fixture()
def api(fabrica, monkeypatch):
    monkeypatch.delenv("INTERNAL_API_KEY", raising=False)  # un .env local no debe afectar a las pruebas
    def _get_db():
        sesion = fabrica()
        try:
            yield sesion
        finally:
            sesion.close()

    app.dependency_overrides[get_db] = _get_db
    # sin 'with': no se ejecuta el arranque (conexión a RabbitMQ)
    yield TestClient(app)
    app.dependency_overrides.clear()
