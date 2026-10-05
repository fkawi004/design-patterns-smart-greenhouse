from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select

from src.infrastructure.db import SessionLocal
from src.infrastructure.persistence.models import DeviceRow, ReadingRow
from src.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_phase_5_test_data() -> Generator[None, None, None]:
    _clean_rows()
    yield
    _clean_rows()


def _clean_rows() -> None:
    with SessionLocal() as session:
        session.execute(delete(DeviceRow).where(DeviceRow.display_name.like("Phase 5 test%")))
        session.commit()


def _create_sensor() -> DeviceRow:
    with SessionLocal() as session:
        row = DeviceRow(
            device_type="moisture_sensor",
            role="sensor",
            device_family="simulation",
            display_name="Phase 5 test moisture",
            default_config={"protocol": "simulation"},
            sampling_interval_seconds=10,
            tracking_enabled=False,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        session.expunge(row)
        return row


def test_read_endpoint_appends_persisted_history() -> None:
    device = _create_sensor()

    first = client.post(f"/api/sensors/{device.id}/read")
    second = client.post(f"/api/sensors/{device.id}/read")
    history = client.get(f"/api/sensors/{device.id}/readings?limit=10")

    assert first.status_code == 201
    assert second.status_code == 201
    assert history.status_code == 200
    assert len(history.json()) == 2
    assert {item["source"] for item in history.json()} == {"simulation"}
    assert {item["device_id"] for item in history.json()} == {str(device.id)}
    with SessionLocal() as session:
        count = session.scalar(
            select(func.count()).select_from(ReadingRow).where(ReadingRow.device_id == device.id)
        )
        assert count == 2


def test_sampling_patch_persists_and_validates_minimum() -> None:
    device = _create_sensor()

    invalid = client.patch(
        f"/api/devices/{device.id}/sampling",
        json={"sampling_interval_seconds": 4, "tracking_enabled": True},
    )
    updated = client.patch(
        f"/api/devices/{device.id}/sampling",
        json={"sampling_interval_seconds": 15, "tracking_enabled": True},
    )

    assert invalid.status_code == 400
    assert updated.status_code == 200
    assert updated.json()["sampling_interval_seconds"] == 15
    assert updated.json()["tracking_enabled"] is True
    with SessionLocal() as session:
        stored = session.get(DeviceRow, device.id)
        assert stored is not None
        assert stored.sampling_interval_seconds == 15
        assert stored.tracking_enabled is True
