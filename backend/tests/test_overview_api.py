from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from src.infrastructure.db import SessionLocal
from src.infrastructure.persistence.models import DeviceRow, LocationRow, ReadingRow, ZoneRow
from src.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_phase_7_test_data() -> Generator[None, None, None]:
    _clean_rows()
    yield
    _clean_rows()


def _clean_rows() -> None:
    with SessionLocal() as session:
        session.execute(delete(DeviceRow).where(DeviceRow.display_name.like("Phase 7 test%")))
        locations = session.scalars(
            select(LocationRow).where(LocationRow.name.like("Phase 7 test%"))
        ).all()
        for location in locations:
            session.delete(location)
        session.commit()


def _seed_overview() -> tuple[LocationRow, DeviceRow, DeviceRow]:
    now = datetime(2026, 10, 27, 12, 0, tzinfo=UTC)
    with SessionLocal() as session:
        location = LocationRow(name="Phase 7 test location")
        session.add(location)
        session.flush()
        measured_zone = ZoneRow(
            location_id=location.id,
            name="Measured zone",
            moisture_threshold_low=0.3,
            moisture_threshold_high=0.5,
            schedule={},
        )
        empty_zone = ZoneRow(
            location_id=location.id,
            name="Empty zone",
            moisture_threshold_low=0.2,
            moisture_threshold_high=0.45,
            schedule={},
        )
        session.add_all([measured_zone, empty_zone])
        session.flush()
        assigned_sensor = DeviceRow(
            device_type="moisture_sensor",
            role="sensor",
            device_family="simulation",
            display_name="Phase 7 test assigned sensor",
            default_config={"protocol": "simulation"},
            zone_id=measured_zone.id,
            location_id=location.id,
            sampling_interval_seconds=45,
            tracking_enabled=False,
        )
        assigned_actuator = DeviceRow(
            device_type="water_pump",
            role="actuator",
            device_family="simulation",
            display_name="Phase 7 test assigned actuator",
            default_config={"protocol": "simulation"},
            zone_id=measured_zone.id,
            location_id=location.id,
            sampling_interval_seconds=300,
            tracking_enabled=True,
        )
        unassigned_sensor = DeviceRow(
            device_type="moisture_sensor",
            role="sensor",
            device_family="simulation",
            display_name="Phase 7 test unassigned sensor",
            default_config={"protocol": "simulation"},
            sampling_interval_seconds=60,
            tracking_enabled=False,
        )
        session.add_all([assigned_sensor, assigned_actuator, unassigned_sensor])
        session.flush()
        session.add_all(
            [
                ReadingRow(
                    device_id=assigned_sensor.id,
                    value=0.44,
                    unit="vwc",
                    source="mqtt",
                    recorded_at=now - timedelta(minutes=1),
                ),
                ReadingRow(
                    device_id=assigned_sensor.id,
                    value=0.4,
                    unit="vwc",
                    source="simulation",
                    recorded_at=now,
                ),
                ReadingRow(
                    device_id=unassigned_sensor.id,
                    value=0.1,
                    unit="vwc",
                    source="vendor",
                    recorded_at=now,
                ),
            ]
        )
        session.commit()
        for row in (location, assigned_sensor, unassigned_sensor):
            session.refresh(row)
            session.expunge(row)
        return location, assigned_sensor, unassigned_sensor


def test_overview_returns_strategy_and_readings() -> None:
    location, assigned_sensor, unassigned_sensor = _seed_overview()

    before = client.get(f"/api/locations/{location.id}/overview")

    assert before.status_code == 200
    body = before.json()
    assert body["location"]["name"] == "Phase 7 test location"
    assert body["strategy_key"] is None
    assert body["last_recommendation"] is None
    assert body["device_counts"] == {"sensor": 1, "actuator": 1}
    device_ids = {
        device["id"] for zone in body["zones"] for device in zone["devices"]
    }
    assert str(assigned_sensor.id) in device_ids
    assert str(unassigned_sensor.id) not in device_ids
    measured = next(zone for zone in body["zones"] if zone["name"] == "Measured zone")
    reading = measured["latest_readings"][0]
    assert reading["device_id"] == str(assigned_sensor.id)
    assert reading["value"] == 0.4
    assert reading["unit"] == "vwc"
    assert reading["tracking_enabled"] is False
    assert reading["sampling_interval_seconds"] == 45
    empty = next(zone for zone in body["zones"] if zone["name"] == "Empty zone")
    assert empty["devices"] == []
    assert empty["latest_readings"] == []

    saved = client.put(
        f"/api/locations/{location.id}/automation",
        json={"strategy_key": "aggressive"},
    )
    evaluated = client.post(f"/api/locations/{location.id}/automation/evaluate")
    after = client.get(f"/api/locations/{location.id}/overview")

    assert saved.status_code == 200
    assert evaluated.status_code == 200
    assert after.status_code == 200
    assert after.json()["strategy_key"] == "aggressive"
    assert after.json()["last_recommendation"] == {
        "action": evaluated.json()["action"],
        "reason": evaluated.json()["reason"],
    }


def test_overview_returns_404_for_unknown_location() -> None:
    response = client.get(f"/api/locations/{uuid4()}/overview")

    assert response.status_code == 404
