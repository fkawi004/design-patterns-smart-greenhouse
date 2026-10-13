from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from src.infrastructure.db import SessionLocal
from src.infrastructure.persistence.models import (
    AutomationRuleRow,
    DeviceRow,
    LocationRow,
    ReadingRow,
    ZoneRow,
)
from src.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_phase_6_test_data() -> Generator[None, None, None]:
    _clean_rows()
    yield
    _clean_rows()


def _clean_rows() -> None:
    with SessionLocal() as session:
        session.execute(delete(DeviceRow).where(DeviceRow.display_name.like("Phase 6 test%")))
        locations = session.scalars(
            select(LocationRow).where(LocationRow.name.like("Phase 6 test%"))
        ).all()
        for location in locations:
            session.delete(location)
        session.commit()


def _seed_location() -> tuple[LocationRow, AutomationRuleRow]:
    with SessionLocal() as session:
        location = LocationRow(name="Phase 6 test location")
        session.add(location)
        session.flush()
        wet_zone = ZoneRow(
            location_id=location.id,
            name="Measured zone",
            moisture_threshold_low=0.3,
            moisture_threshold_high=0.5,
            schedule={},
        )
        empty_zone = ZoneRow(
            location_id=location.id,
            name="No sensor zone",
            moisture_threshold_low=0.2,
            moisture_threshold_high=0.45,
            schedule={},
        )
        session.add_all([wet_zone, empty_zone])
        session.flush()
        sensor = DeviceRow(
            device_type="moisture_sensor",
            role="sensor",
            device_family="simulation",
            display_name="Phase 6 test sensor",
            default_config={"protocol": "simulation"},
            zone_id=wet_zone.id,
            location_id=location.id,
            sampling_interval_seconds=60,
            tracking_enabled=False,
        )
        rule = AutomationRuleRow(
            location_id=location.id,
            strategy_key="conservative",
            parameters={},
        )
        session.add_all([sensor, rule])
        session.flush()
        session.add(
            ReadingRow(
                device_id=sensor.id,
                value=0.4,
                unit="vwc",
                source="simulation",
            )
        )
        session.commit()
        session.refresh(location)
        session.refresh(rule)
        session.expunge(location)
        session.expunge(rule)
        return location, rule


def test_evaluate_uses_saved_strategy_latest_reading_and_zone_thresholds() -> None:
    location, _ = _seed_location()

    conservative = client.post(f"/api/locations/{location.id}/automation/evaluate")
    saved = client.put(
        f"/api/locations/{location.id}/automation",
        json={"strategy_key": "aggressive"},
    )
    aggressive = client.post(f"/api/locations/{location.id}/automation/evaluate")

    assert conservative.status_code == 200
    assert conservative.json()["action"] == "wait"
    assert "no moisture sensor reading in this zone" in conservative.json()["reason"]
    assert saved.status_code == 200
    assert aggressive.status_code == 200
    assert aggressive.json()["strategy_key"] == "aggressive"
    assert aggressive.json()["action"] == "irrigate"
    with SessionLocal() as session:
        persisted = session.scalar(
            select(AutomationRuleRow).where(AutomationRuleRow.location_id == location.id)
        )
        assert persisted is not None
        assert persisted.strategy_key == "aggressive"


def test_automation_rejects_unknown_key_and_missing_location() -> None:
    location, _ = _seed_location()

    unknown = client.put(
        f"/api/locations/{location.id}/automation",
        json={"strategy_key": "mystery"},
    )
    missing = client.post(
        "/api/locations/00000000-0000-0000-0000-000000000001/automation/evaluate"
    )

    assert unknown.status_code == 400
    assert missing.status_code == 404
