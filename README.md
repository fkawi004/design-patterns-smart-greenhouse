# Design Patterns Smart Greenhouse

A runnable three-tier course project with a FastAPI backend, PostgreSQL migrations, and a React + TypeScript dashboard. Phase 6 uses pluggable Strategy policies to evaluate the latest saved sensor readings against each zone's thresholds.

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

The migrations create the shared `devices` table, device families, locations, zones, device assignment fields, append-only `sensor_readings` history, and one persisted `automation_rules` strategy per location. The database data remains in a Docker volume after containers restart.

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
- Automation API: `PUT /api/locations/{id}/automation` and `POST /api/locations/{id}/automation/evaluate`

Swagger at `/docs` and ReDoc at `/redoc` are intentionally disabled.

## Checks

```powershell
docker compose exec backend ruff check .
docker compose exec backend pytest
docker compose exec backend alembic current
docker compose exec frontend npm run lint
docker compose exec frontend npm run build
```

See [the phase order](docs/phases/README.md), [the Strategy notes](docs/patterns/strategy.md), and [the Phase 6 answers](docs/phases/phase-06/questions.md).
