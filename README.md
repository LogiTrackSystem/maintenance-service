# Maintenance Service

Microservicio de mantenimiento preventivo de la flota. Consume `telemetry.raw` (publicado por Tracking Ingestion Service) y evalúa reglas simples por tipo de vehículo (umbral de kilometraje, temperatura de motor, códigos OBD2) para programar mantenimiento automáticamente y alertar sobre anomalías. Mantiene el historial de intervenciones realizadas.

## Requisitos

- Python 3.11+
- PostgreSQL
- RabbitMQ
- Fleet Service corriendo (se consulta por REST para conocer el tipo de vehículo)

## Setup

1. Crear la base de datos `maintenance_db`.
2. Copiar `.env.example` a `.env` y completar con tus credenciales reales.
3. `python -m venv venv && venv\Scripts\activate`
4. `pip install -r requirements.txt`
5. `alembic upgrade head`
6. `uvicorn app.main:app --reload --port 8005`

## Endpoints

- `POST /programas/` — crea un programa de mantenimiento manualmente.
- `GET /programas/{vehiculo_id}` — lista los programas de mantenimiento de un vehículo.
- `POST /intervenciones/` — registra una intervención de mantenimiento realizada.
- `GET /intervenciones/{vehiculo_id}` — historial de intervenciones de un vehículo.
- `GET /health` — healthcheck.

## Eventos

- **Consume:** `telemetry.raw`
- **Publica:** `maintenance.alert`