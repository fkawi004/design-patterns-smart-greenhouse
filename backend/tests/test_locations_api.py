from collections.abc import Generator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from src.infrastructure.db import SessionLocal
from src.infrastructure.persistence.models import DeviceRow, LocationRow
from src.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_phase_4_test_data() -> Generator[None, None, None]:
    _clean_test_rows()
    yield
    _clean_test_rows()


def _clean_test_rows() -> None:
    with SessionLocal() as session:
        session.execute(delete(DeviceRow).where(DeviceRow.display_name.like("Phase 4 test%")))
        session.execute(delete(LocationRow).where(LocationRow.name.like("Phase 4 test%")))
        session.commit()


def _create_location(name: str, zone_names: tuple[str, ...] = ("North",)) -> dict:
    response = client.post(
        "/api/locations/config",
        json={
            "location_name": name,
            "zones": [
                {
                    "name": zone_name,
                    "moisture_threshold_low": 0.2,
                    "moisture_threshold_high": 0.5,
                    "schedule": {"watering": "08:00"},
                }
                for zone_name in zone_names
            ],
        },
    )
    assert response.status_code == 201
    return response.json()


def _create_device(name: str) -> UUID:
    with SessionLocal() as session:
        row = DeviceRow(
            device_type="moisture_sensor",
            role="sensor",
            device_family="simulation",
            display_name=name,
            default_config={},
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return row.id


def test_create_and_get_config_with_location_ids() -> None:
    created = _create_location("Phase 4 test Main", ("North", "South"))
    location_id = created["location"]["id"]

    response = client.get(f"/api/locations/{location_id}/config")

    assert response.status_code == 200
    payload = response.json()
    assert payload["location"] == {"id": location_id, "name": "Phase 4 test Main"}
    assert {zone["name"] for zone in payload["zones"]} == {"North", "South"}
    assert {zone["location_id"] for zone in payload["zones"]} == {location_id}


def test_invalid_config_returns_400_without_persisting() -> None:
    response = client.post(
        "/api/locations/config",
        json={
            "location_name": "Phase 4 test Invalid",
            "zones": [
                {
                    "name": "North",
                    "moisture_threshold_low": 0.8,
                    "moisture_threshold_high": 0.2,
                }
            ],
        },
    )

    assert response.status_code == 400
    assert all(
        item["name"] != "Phase 4 test Invalid" for item in client.get("/api/locations").json()
    )


def test_assign_devices_to_zone_and_unassign() -> None:
    config = _create_location("Phase 4 test Assignment", ("One", "Two"))
    location_id = config["location"]["id"]
    first_zone_id, second_zone_id = [zone["id"] for zone in config["zones"]]
    first_device = _create_device("Phase 4 test device one")
    second_device = _create_device("Phase 4 test device two")
    other_device = _create_device("Phase 4 test device elsewhere")

    for device_id in (first_device, second_device):
        response = client.patch(
            f"/api/devices/{device_id}/zone",
            json={"zone_id": second_zone_id},
        )
        assert response.status_code == 200
        assert response.json()["location_id"] == location_id
    client.patch(f"/api/devices/{other_device}/zone", json={"zone_id": first_zone_id})

    listed = client.get(f"/api/locations/{location_id}/zones/{second_zone_id}/devices")
    assert listed.status_code == 200
    assert {item["id"] for item in listed.json()} == {str(first_device), str(second_device)}

    unassigned = client.patch(
        f"/api/devices/{first_device}/zone",
        json={"zone_id": None},
    )
    assert unassigned.status_code == 200
    assert unassigned.json()["zone_id"] is None
    assert unassigned.json()["location_id"] is None


def test_list_and_delete_location_clears_assignment() -> None:
    first = _create_location("Phase 4 test First")
    second = _create_location("Phase 4 test Second")
    first_id = first["location"]["id"]
    device_id = _create_device("Phase 4 test delete location device")
    client.patch(
        f"/api/devices/{device_id}/zone",
        json={"zone_id": first["zones"][0]["id"]},
    )

    listed_ids = {item["id"] for item in client.get("/api/locations").json()}
    assert {first_id, second["location"]["id"]} <= listed_ids
    assert client.delete(f"/api/locations/{first_id}").status_code == 204
    assert client.get(f"/api/locations/{first_id}/config").status_code == 404
    assert client.get(f"/api/locations/{second['location']['id']}/config").status_code == 200

    with SessionLocal() as session:
        device = session.get(DeviceRow, device_id)
        assert device is not None
        assert device.zone_id is None
        assert device.location_id is None


def test_manage_zones_and_protect_last_zone() -> None:
    config = _create_location("Phase 4 test Zone management")
    location_id = config["location"]["id"]
    first_zone_id = config["zones"][0]["id"]
    add_response = client.post(
        f"/api/locations/{location_id}/zones",
        json={
            "name": "South",
            "moisture_threshold_low": 0.25,
            "moisture_threshold_high": 0.55,
            "schedule": {},
        },
    )
    assert add_response.status_code == 201
    second_zone_id = add_response.json()["id"]

    invalid_update = client.patch(
        f"/api/locations/{location_id}/zones/{second_zone_id}",
        json={
            "name": "South changed",
            "moisture_threshold_low": 0.8,
            "moisture_threshold_high": 0.3,
            "schedule": {},
        },
    )
    assert invalid_update.status_code == 400
    stored = client.get(f"/api/locations/{location_id}/config").json()
    assert next(zone for zone in stored["zones"] if zone["id"] == second_zone_id)["name"] == "South"

    device_id = _create_device("Phase 4 test delete zone device")
    client.patch(f"/api/devices/{device_id}/zone", json={"zone_id": second_zone_id})
    assert client.delete(f"/api/locations/{location_id}/zones/{second_zone_id}").status_code == 204
    with SessionLocal() as session:
        device = session.get(DeviceRow, device_id)
        assert device is not None
        assert device.zone_id is None
        assert device.location_id is None

    rejected = client.delete(f"/api/locations/{location_id}/zones/{first_zone_id}")
    assert rejected.status_code == 400
    assert len(client.get(f"/api/locations/{location_id}/config").json()["zones"]) == 1
