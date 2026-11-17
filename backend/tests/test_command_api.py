from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select

from src.infrastructure.db import SessionLocal
from src.infrastructure.persistence.models import (
    ActuatorExecutionLogRow,
    ActuatorStateRow,
    CommandLogRow,
    DeviceRow,
)
from src.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_phase_10_test_data() -> Generator[None, None, None]:
    _clean_rows()
    yield
    _clean_rows()


def _clean_rows() -> None:
    with SessionLocal() as session:
        session.execute(delete(DeviceRow).where(DeviceRow.display_name.like("Phase 10 test%")))
        session.commit()


def _seed_device(
    *,
    role: str = "actuator",
    device_type: str = "water_pump",
    state: str = "idle",
    updated_at: datetime | None = None,
) -> DeviceRow:
    with SessionLocal() as session:
        device = DeviceRow(
            device_type=device_type,
            role=role,
            device_family="simulation",
            display_name=f"Phase 10 test {device_type} {uuid4()}",
            default_config={"protocol": "simulation"},
            sampling_interval_seconds=300,
            tracking_enabled=True,
        )
        session.add(device)
        session.flush()
        if role == "actuator":
            session.add(
                ActuatorStateRow(
                    device_id=device.id,
                    state=state,
                    updated_at=updated_at or datetime.now(UTC),
                )
            )
        session.commit()
        session.refresh(device)
        session.expunge(device)
        return device


def _post(command_type: str, device_id: object, payload: dict | None = None):
    return client.post(
        "/api/commands",
        json={
            "command_type": command_type,
            "device_id": str(device_id),
            "payload": payload or {},
        },
    )


def test_illegal_command_rejected_logged_without_state_or_apply() -> None:
    actuator = _seed_device(state="idle")

    response = _post("stop_pump", actuator.id)

    assert response.status_code == 409
    assert response.json()["status"] == "rejected"
    with SessionLocal() as session:
        state = session.scalar(
            select(ActuatorStateRow.state).where(ActuatorStateRow.device_id == actuator.id)
        )
        command_count = session.scalar(
            select(func.count()).select_from(CommandLogRow).where(
                CommandLogRow.device_id == actuator.id
            )
        )
        execution_count = session.scalar(
            select(func.count()).select_from(ActuatorExecutionLogRow).where(
                ActuatorExecutionLogRow.device_id == actuator.id
            )
        )
    assert state == "idle"
    assert command_count == 1
    assert execution_count == 0


def test_start_pump_transitions_to_running_and_logs_success() -> None:
    actuator = _seed_device(state="idle")

    response = _post("start_pump", actuator.id)

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    with SessionLocal() as session:
        state = session.scalar(
            select(ActuatorStateRow.state).where(ActuatorStateRow.device_id == actuator.id)
        )
        command = session.scalar(
            select(CommandLogRow).where(CommandLogRow.device_id == actuator.id)
        )
        execution = session.scalar(
            select(ActuatorExecutionLogRow).where(
                ActuatorExecutionLogRow.device_id == actuator.id
            )
        )
    assert state == "running"
    assert command is not None and command.status == "success"
    assert execution is not None and execution.success is True


def test_decorator_failure_logs_failed_and_leaves_state_unchanged() -> None:
    actuator = _seed_device(
        state="running",
        updated_at=datetime.now(UTC) - timedelta(minutes=31),
    )

    response = _post("stop_pump", actuator.id)

    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    assert response.json()["error_message"] == "Max run time exceeded"
    with SessionLocal() as session:
        state = session.scalar(
            select(ActuatorStateRow.state).where(ActuatorStateRow.device_id == actuator.id)
        )
        execution = session.scalar(
            select(ActuatorExecutionLogRow).where(
                ActuatorExecutionLogRow.device_id == actuator.id
            )
        )
    assert state == "running"
    assert execution is not None and execution.success is False


def test_unknown_missing_and_non_actuator_commands_write_no_rows() -> None:
    actuator = _seed_device()
    sensor = _seed_device(role="sensor", device_type="moisture_sensor")

    unknown = _post("open_portal", actuator.id)
    missing = _post("start_pump", uuid4())
    sensor_response = _post("start_pump", sensor.id)

    assert unknown.status_code == 400
    assert missing.status_code == 404
    assert sensor_response.status_code == 404
    with SessionLocal() as session:
        count = session.scalar(
            select(func.count()).select_from(CommandLogRow).where(
                CommandLogRow.device_id.in_([actuator.id, sensor.id])
            )
        )
    assert count == 0


def test_history_is_newest_first_and_limit_is_applied() -> None:
    pump = _seed_device(state="idle")
    light = _seed_device(device_type="grow_light", state="running")
    assert _post("start_pump", pump.id).status_code == 200
    latest = _post("set_light_level", light.id, {"level": 35})

    response = client.get("/api/commands?limit=1")

    assert latest.status_code == 200
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == latest.json()["id"]
