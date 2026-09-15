from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference

from src.infrastructure.settings import get_settings
from src.interfaces.api.health import router as health_router
from src.interfaces.api.sensors import router as sensors_router

settings = get_settings()

app = FastAPI(
    title="Smart Greenhouse API",
    description="API foundation for the Design Patterns smart greenhouse project.",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
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
