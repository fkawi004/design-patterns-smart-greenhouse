from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from src.application.readings.sampler import SimulationSampler
from src.application.readings.service import ReadingIngest
from src.domain.devices.entity import Device
from src.domain.sensors.reading import Reading
from src.infrastructure.adapters.sensors.selector import SensorAdapterSelector


class FakeReadingRepository:
    def __init__(self, devices: list[Device]) -> None:
        self.devices = {device.id: device for device in devices if device.id is not None}
        self.readings: dict[UUID, list[Reading]] = {}

    def get_device(self, device_id: UUID) -> Device | None:
        return self.devices.get(device_id)

    def insert(self, reading: Reading) -> Reading:
        self.readings.setdefault(reading.device_id, []).append(reading)
        return reading

    def list_for_device(self, device_id: UUID, limit: int = 20) -> list[Reading]:
        return list(reversed(self.readings.get(device_id, [])))[:limit]

    def latest_for_device(self, device_id: UUID) -> Reading | None:
        rows = self.readings.get(device_id, [])
        return rows[-1] if rows else None

    def list_tracking_sensors(self) -> list[Device]:
        return [
            device
            for device in self.devices.values()
            if device.role == "sensor" and device.tracking_enabled
        ]

    def update_sampling(
        self,
        device_id: UUID,
        sampling_interval_seconds: int,
        tracking_enabled: bool,
    ) -> Device | None:
        device = self.devices.get(device_id)
        if device is None:
            return None
        updated = replace(
            device,
            sampling_interval_seconds=sampling_interval_seconds,
            tracking_enabled=tracking_enabled,
        )
        self.devices[device_id] = updated
        return updated


def make_sensor(
    protocol: str,
    tracking_enabled: bool = True,
) -> Device:
    return Device(
        id=uuid4(),
        device_type="moisture_sensor",
        role="sensor",
        device_family="simulation" if protocol == "simulation" else "edge",
        display_name=f"{protocol} sensor",
        default_config={"protocol": protocol},
        sampling_interval_seconds=60,
        tracking_enabled=tracking_enabled,
    )


def test_sampler_respects_interval_tracking_and_protocol() -> None:
    simulation = make_sensor("simulation")
    disabled = make_sensor("simulation", tracking_enabled=False)
    mqtt = make_sensor("mqtt")
    repository = FakeReadingRepository([simulation, disabled, mqtt])
    ingest = ReadingIngest(repository, SensorAdapterSelector())
    sampler = SimulationSampler(repository, ingest)
    start = datetime(2026, 10, 5, 12, 0, tzinfo=UTC)

    assert sampler.run_once(start) == 1
    assert sampler.run_once(start + timedelta(seconds=30)) == 0
    assert sampler.run_once(start + timedelta(seconds=60)) == 1

    assert len(repository.readings[simulation.id]) == 2
    assert disabled.id not in repository.readings
    assert mqtt.id not in repository.readings
