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

---

<!-- entrega-final -->

## Descripción

Programas e intervenciones de mantenimiento; genera alertas y retira vehículos cuando la telemetría supera los umbrales.

- **Puerto local:** 8005   ·   **Despliegue activo:** <https://logitrack-maintenance.onrender.com> (`/health` y `/metrics` públicos)
- **Imagen Docker:** `<usuario-dockerhub>/logitrack-maintenance`   ·   **Repositorio de CI/CD:** `LogiTrackSystem/pipelines`

## Variables de entorno

Copia `.env.example` como `.env` y completa los valores. El `.env` **no se sube** al repositorio.

| Variable | Para qué sirve |
|---|---|
| `DATABASE_URL` | Conexión a la base PostgreSQL del servicio (`postgresql://usuario:clave@host:5432/<base>`). Es un secreto. |
| `RABBITMQ_URL` | URL AMQP del bus de eventos RabbitMQ (CloudAMQP en producción). Es un secreto. |
| `FLEET_SERVICE_URL` | URL base de Fleet Service, sin barra final (en local `http://localhost:<puerto>`). |
| `INTERNAL_API_KEY` | Clave compartida entre el gateway y los servicios: exige la cabecera `X-Internal-Key` en todas las rutas salvo `/health` y `/metrics`. Vacía = sin restricción (solo local). Es un secreto. |

## Documentación de la API

- **Local** (sin `INTERNAL_API_KEY`): <http://localhost:8005/docs> (Swagger) y `http://localhost:8005/openapi.json`.
- **Producción:** el servicio solo atiende peticiones que llegan por el gateway (con `INTERNAL_API_KEY` activa su `/docs` no es público); la documentación de todas las rutas está en <https://logitrack-gateway.onrender.com/docs>.

## Base de datos

- Migraciones con Alembic (`alembic/`): `alembic upgrade head` (el `Dockerfile` ya lo ejecuta al arrancar).
- `db/esquema.sql`: esquema completo de `maintenance_db` generado desde las migraciones.
- Datos de ejemplo: este servicio se alimenta de eventos y llamadas de otros servicios; se generan ejecutando el flujo completo (por ejemplo `_pruebas/casos.py` del proyecto).
- Respaldo y restauración: ver `db/README.md`.

## Pruebas

Con el entorno virtual activo y `pip install -r requirements-dev.txt`:

```
pytest tests/unit                    # 2 pruebas unitarias
pytest tests/integration             # 1 prueba de integración
pytest --cov=app --cov-report=term   # toda la suite con cobertura
```

| Prueba | Qué verifica |
|---|---|
| Unitaria 1 | `events._crear_o_actualizar_programa` |
| Unitaria 2 | `events._procesar_telemetry_raw` |
| Integración | creación de un programa y una intervención y su consulta por vehículo |

Archivos: `tests/unit/` y `tests/integration/` (test_programa_mantenimiento.py, test_telemetria_umbrales.py, test_flujo_mantenimiento.py). Cobertura de `app/` medida: **≈ 81 %**; en cada push y Pull Request GitHub Actions la recalcula y guarda `coverage.xml` como artefacto (`cobertura-maintenance`).

## Métricas y monitoreo

Expone `GET /metrics` (formato Prometheus: `http_requests_total` y `http_request_duration_*`). Prometheus y el dashboard de Grafana están en el repositorio `logitrack-monitoring`.

## CI/CD

- `.github/workflows/pr.yml`: en cada push (rama distinta de `main`) y en cada Pull Request a `main` ejecuta el CI reutilizable (lint, pruebas con cobertura, `docker build` y prueba de arranque).
- `.github/workflows/deploy.yml`: al fusionar en `main`, y solo con las pruebas en verde, publica la imagen en Docker Hub y despliega en Render (con verificación de `/health` y rollback manual).
- Detalle y estrategia de ramas: `CICD.md` en el repositorio `LogiTrackSystem/pipelines`.

