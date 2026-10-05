# Design Patterns Smart Greenhouse

A runnable three-tier course project with a FastAPI backend, PostgreSQL migrations, and a React + TypeScript dashboard. Phase 5 uses Adapter ports for simulated, vendor-stub, and MQTT-shaped sensor readings, then saves every reading for later history and Strategy work.

## Prerequisites

- Docker Desktop with Docker Compose
- Git

## First-time setup

Copy the example environment file, build the containers, apply the migrations, and start the application:

```powershell
Copy-Item .env.example .env
docker compose up --build -d
docker compose exec backend alembic upgrade head
```

The migrations create the shared `devices` table, device families, locations, zones, device assignment fields, and append-only `sensor_readings` history. The database data remains in a Docker volume after containers restart.

## Daily start

Start or stop the complete development stack from the repository root:

```powershell
docker compose up -d
docker compose down
```

The backend and frontend source directories are mounted into their development containers, so both servers reload when code changes.

## Development URLs

- Dashboard: http://localhost:5173/dashboard
- API discovery: http://localhost:8000/
- Health: http://localhost:8000/health
- Scalar API reference: http://localhost:8000/scalar
- OpenAPI JSON: http://localhost:8000/openapi.json
- Sensors API: http://localhost:8000/api/sensors
- Sensor reading API: `POST /api/sensors/{id}/read` and `GET /api/sensors/{id}/readings`
- Devices API: http://localhost:8000/api/devices
- Locations API: http://localhost:8000/api/locations

Swagger at `/docs` and ReDoc at `/redoc` are intentionally disabled.

## Checks

```powershell
docker compose exec backend ruff check .
docker compose exec backend pytest
docker compose exec backend alembic current
docker compose exec frontend npm run lint
docker compose exec frontend npm run build
```

See [the phase order](docs/phases/README.md), [the Adapter notes](docs/patterns/adapter.md), and [the Phase 5 answers](docs/phases/phase-05/questions.md).
