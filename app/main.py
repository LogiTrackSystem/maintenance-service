from contextlib import asynccontextmanager
from fastapi import FastAPI

from .routers import programas, intervenciones
from .events import iniciar_consumidor


@asynccontextmanager
async def lifespan(app: FastAPI):
    connection = await iniciar_consumidor()
    yield
    await connection.close()


app = FastAPI(title="Maintenance Service", lifespan=lifespan)
app.include_router(programas.router)
app.include_router(intervenciones.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "maintenance-service"}