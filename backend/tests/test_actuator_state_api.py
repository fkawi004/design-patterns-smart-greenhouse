from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from src.domain.devices.entity import Device
from src.infrastructure.db import SessionLocal
from src.infrastructure.persistence.device_repository import SqlAlchemyDeviceRepository
from src.infrastructure.persistence.models import ActuatorStateRow, DeviceRow
from src.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_phase_8_test_data() -> Generator[None, None, None]:
    _clean_rows()
    yield
    _clean_rows()


def _clean_rows() -> None:
    with SessionLocal() as session:
        session.execute(delete(DeviceRow).where(DeviceRow.display_name.like("Phase 8 test%")))
        session.commit()


def _seed_devices() -> tuple[DeviceRow, DeviceRow]:
    with SessionLocal() as session:
        actuator = DeviceRow(
            device_type="water_pump",
            role="actuator",
            device_family="simulation",
            display_name="Phase 8 test pump",
            default_config={"protocol": "simulation"},
            sampling_interval_seconds=300,
            tracking_enabled=True,
        )
        sensor = DeviceRow(
            device_type="moisture_sensor",
            role="sensor",
            device_family="simulation",
            display_name="Phase 8 test sensor",
            default_config={"protocol": "simulation"},
            sampling_interval_seconds=60,
            tracking_enabled=True,
        )
        session.add_all([actuator, sensor])
        session.flush()
        session.add(ActuatorStateRow(device_id=actuator.id, state="idle"))
        session.commit()
        for row in (actuator, sensor):
            session.refresh(row)
            session.expunge(row)
        return actuator, sensor


def test_device_api_exposes_actuator_state_and_allowed_commands() -> None:
    actuator, sensor = _seed_devices()

    response = client.get("/api/devices?family=simulation")

    assert response.status_code == 200
    devices = {item["id"]: item for item in response.json()}
    assert devices[str(actuator.id)]["state"] == "idle"
    assert devices[str(actuator.id)]["allowed_commands"] == [
        "start",
        "enter_maintenance",
        "report_error",
        "power_off",
    ]
    assert devices[str(sensor.id)]["state"] is None
    assert devices[str(sensor.id)]["allowed_commands"] == []


def test_new_actuator_is_created_with_idle_state() -> None:
    with SessionLocal() as session:
        saved = SqlAlchemyDeviceRepository(session).save_many(
            [
                Device(
                    device_type="water_pump",
                    role="actuator",
                    device_family="simulation",
                    display_name="Phase 8 test provisioned pump",
                    default_config={"protocol": "simulation"},
                )
            ]
        )

    assert saved[0].state == "idle"
    with SessionLocal() as session:
        persisted = session.scalar(
            select(ActuatorStateRow.state).where(
                ActuatorStateRow.device_id == saved[0].id
            )
        )
    assert persisted == "idle"


def test_legal_transition_is_persisted() -> None:
    actuator, _ = _seed_devices()

    response = client.post(
        f"/api/devices/{actuator.id}/transition",
        json={"target": "running"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "device_id": str(actuator.id),
        "state": "running",
        "allowed_commands": ["stop", "report_error", "power_off"],
    }
    with SessionLocal() as session:
        persisted = session.scalar(
            select(ActuatorStateRow.state).where(ActuatorStateRow.device_id == actuator.id)
        )
    assert persisted == "running"


def test_illegal_transition_does_not_update_row() -> None:
    actuator, _ = _seed_devices()
    first = client.post(
        f"/api/devices/{actuator.id}/transition",
        json={"target": "running"},
    )

    rejected = client.post(
        f"/api/devices/{actuator.id}/transition",
        json={"target": "maintenance"},
    )

    assert first.status_code == 200
    assert rejected.status_code == 409
    assert "cannot transition" in rejected.json()["detail"]
    with SessionLocal() as session:
        persisted = session.scalar(
            select(ActuatorStateRow.state).where(ActuatorStateRow.device_id == actuator.id)
        )
    assert persisted == "running"


def test_transition_returns_404_for_non_actuator() -> None:
    _, sensor = _seed_devices()

    sensor_response = client.post(
        f"/api/devices/{sensor.id}/transition",
        json={"target": "running"},
    )
    missing_response = client.post(
        f"/api/devices/{uuid4()}/transition",
        json={"target": "running"},
    )

    assert sensor_response.status_code == 404
    assert missing_response.status_code == 404
