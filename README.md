# Design Patterns Smart Greenhouse

A runnable three-tier course project with a FastAPI backend, PostgreSQL migrations, and a React + TypeScript dashboard. Phase 4 uses Builder to create valid location configurations while keeping the sensor and device-family features from earlier phases.

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

The migrations create the shared `devices` table, device families, locations, zones, and device assignment fields. The database data remains in a Docker volume after containers restart.

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

See [the phase order](docs/phases/README.md), [the Builder notes](docs/patterns/builder.md), and [the Phase 4 answers](docs/phases/phase-04/questions.md).
