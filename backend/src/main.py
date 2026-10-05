import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference

from src.application.readings.sampler import SimulationSampler
from src.application.readings.service import ReadingIngest
from src.infrastructure.adapters.sensors.selector import SensorAdapterSelector
from src.infrastructure.db import SessionLocal
from src.infrastructure.persistence.reading_repository import SqlAlchemyReadingRepository
from src.infrastructure.settings import get_settings
from src.interfaces.api.devices import router as devices_router
from src.interfaces.api.health import router as health_router
from src.interfaces.api.locations import router as locations_router
from src.interfaces.api.sensors import router as sensors_router

settings = get_settings()
logger = logging.getLogger(__name__)


async def run_simulation_sampler(stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            with SessionLocal() as session:
                repository = SqlAlchemyReadingRepository(session)
                ingest = ReadingIngest(repository, SensorAdapterSelector())
                SimulationSampler(repository, ingest).run_once(datetime.now(UTC))
        except Exception:
            logger.exception("Simulation sampler tick failed")
        try:
            await asyncio.wait_for(stop.wait(), timeout=1.0)
        except TimeoutError:
            pass


@asynccontextmanager
async def lifespan(_app: FastAPI):
    stop = asyncio.Event()
    task = asyncio.create_task(run_simulation_sampler(stop))
    try:
        yield
    finally:
        stop.set()
        await task


app = FastAPI(
    title="Smart Greenhouse API",
    description="API foundation for the Design Patterns smart greenhouse project.",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(sensors_router)
app.include_router(devices_router)
app.include_router(locations_router)


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {
        "name": "Smart Greenhouse API",
        "api_reference": "/scalar",
        "openapi": "/openapi.json",
    }


@app.get("/scalar", include_in_schema=False)
async def scalar_api_reference():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=f"{app.title} — API Reference",
    )
