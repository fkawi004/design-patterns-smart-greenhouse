# Design Patterns Smart Greenhouse

A runnable three-tier course project with a FastAPI backend, PostgreSQL migrations, and a React + TypeScript dashboard. Phase 3 uses Abstract Factory to provision matching simulation and edge device families while keeping Phase 2 sensor creation.

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

The migrations create the shared `devices` table and add a device family for sensors and actuators. The database data remains in a Docker volume after containers restart.

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

Swagger at `/docs` and ReDoc at `/redoc` are intentionally disabled.

## Checks

```powershell
docker compose exec backend ruff check .
docker compose exec backend pytest
docker compose exec backend alembic current
docker compose exec frontend npm run lint
docker compose exec frontend npm run build
```

See [the phase order](docs/phases/README.md), [the Abstract Factory notes](docs/patterns/abstract-factory.md), and [the Phase 3 answers](docs/phases/phase-03/questions.md).
