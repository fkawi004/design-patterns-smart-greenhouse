from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from src.infrastructure.db import SessionLocal
from src.infrastructure.persistence.models import (
    ActuatorExecutionLogRow,
    ActuatorStateRow,
    DeviceRow,
)
from src.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_phase_9_test_data() -> Generator[None, None, None]:
    _clean_rows()
    yield
    _clean_rows()


def _clean_rows() -> None:
    with SessionLocal() as session:
        session.execute(delete(DeviceRow).where(DeviceRow.display_name.like("Phase 9 test%")))
        session.commit()


def _seed_actuator(
    *,
    state: str = "idle",
    updated_at: datetime | None = None,
) -> DeviceRow:
    with SessionLocal() as session:
        actuator = DeviceRow(
            device_type="water_pump",
            role="actuator",
            device_family="simulation",
            display_name=f"Phase 9 test pump {uuid4()}",
            default_config={"protocol": "simulation"},
            sampling_interval_seconds=300,
            tracking_enabled=True,
        )
        session.add(actuator)
        session.flush()
        session.add(
            ActuatorStateRow(
                device_id=actuator.id,
                state=state,
                updated_at=updated_at or datetime.now(UTC),
            )
        )
        session.commit()
        session.refresh(actuator)
        session.expunge(actuator)
        return actuator


def test_successful_apply_writes_execution_row() -> None:
    actuator = _seed_actuator()

    applied = client.post(
        f"/api/actuators/{actuator.id}/apply",
        json={"command": "unknown_command", "payload": {"level": 2}},
    )
    listed = client.get("/api/actuators/executions?limit=20")

    assert applied.status_code == 204
    assert listed.status_code == 200
    execution = next(
        item for item in listed.json() if item["device_id"] == str(actuator.id)
    )
    assert execution["success"] is True
    assert execution["policy_applied"] == ["logging"]
    assert execution["message"] is None
    with SessionLocal() as session:
        stored = session.scalar(
            select(ActuatorExecutionLogRow).where(
                ActuatorExecutionLogRow.device_id == actuator.id
            )
        )
    assert stored is not None
    assert stored.success is True


def test_blocked_apply_writes_failed_execution_row() -> None:
    actuator = _seed_actuator(
        state="running",
        updated_at=datetime.now(UTC) - timedelta(minutes=31),
    )

    blocked = client.post(
        f"/api/actuators/{actuator.id}/apply",
        json={"command": "anything", "payload": {}},
    )
    listed = client.get("/api/actuators/executions?limit=20")

    assert blocked.status_code == 409
    assert blocked.json()["detail"] == "Max run time exceeded"
    execution = next(
        item for item in listed.json() if item["device_id"] == str(actuator.id)
    )
    assert execution["success"] is False
    assert execution["policy_applied"] == ["maxRunTime", "logging"]
    assert execution["message"] == "Max run time exceeded"


def test_execution_limit_and_missing_actuator() -> None:
    actuator = _seed_actuator()
    for command in ("first", "second"):
        response = client.post(
            f"/api/actuators/{actuator.id}/apply",
            json={"command": command, "payload": {}},
        )
        assert response.status_code == 204

    limited = client.get("/api/actuators/executions?limit=1")
    missing = client.post(
        f"/api/actuators/{uuid4()}/apply",
        json={"command": "anything", "payload": {}},
    )

    assert limited.status_code == 200
    assert len(limited.json()) == 1
    assert missing.status_code == 404
