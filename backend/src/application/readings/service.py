from datetime import datetime
from typing import Protocol
from uuid import UUID

from src.application.readings.dto import ReadingDto, SamplingSettingsDto
from src.application.readings.errors import (
    ReadingDeviceNotFoundError,
    ReadingValidationError,
)
from src.application.readings.mappers import reading_to_dto
from src.domain.devices.entity import Device
from src.domain.sensors.ports import SensorPort
from src.domain.sensors.reading import Reading


class ReadingRepository(Protocol):
    def get_device(self, device_id: UUID) -> Device | None: ...

    def insert(self, reading: Reading) -> Reading: ...

    def list_for_device(self, device_id: UUID, limit: int = 20) -> list[Reading]: ...

    def latest_for_device(self, device_id: UUID) -> Reading | None: ...

    def list_tracking_sensors(self) -> list[Device]: ...

    def update_sampling(
        self,
        device_id: UUID,
        sampling_interval_seconds: int,
        tracking_enabled: bool,
    ) -> Device | None: ...


class AdapterSelector(Protocol):
    def for_device(self, device: Device) -> SensorPort: ...


class ReadingIngest:
    def __init__(self, repository: ReadingRepository, selector: AdapterSelector) -> None:
        self.repository = repository
        self.selector = selector

    def take_reading(
        self,
        device_id: UUID,
        recorded_at: datetime | None = None,
    ) -> ReadingDto:
        device = self._get_device(device_id)
        if device.role != "sensor":
            raise ReadingValidationError("Only sensor devices can be read.")
        reading = self.selector.for_device(device).read(device, recorded_at)
        return self.record(device_id, reading)

    def record(self, device_id: UUID, reading: Reading) -> ReadingDto:
        device = self._get_device(device_id)
        if device.role != "sensor":
            raise ReadingValidationError("Readings can only be stored for sensor devices.")
        if reading.device_id != device_id:
            raise ReadingValidationError("Reading device_id does not match the target device.")
        return reading_to_dto(self.repository.insert(reading))

    def list_readings(self, device_id: UUID, limit: int = 20) -> list[ReadingDto]:
        device = self._get_device(device_id)
        if device.role != "sensor":
            raise ReadingValidationError("Only sensor devices have reading history.")
        return [reading_to_dto(item) for item in self.repository.list_for_device(device_id, limit)]

    def update_sampling(
        self,
        device_id: UUID,
        sampling_interval_seconds: int,
        tracking_enabled: bool,
    ) -> SamplingSettingsDto:
        if sampling_interval_seconds < 5:
            raise ReadingValidationError("Sampling interval must be at least 5 seconds.")
        device = self.repository.update_sampling(
            device_id,
            sampling_interval_seconds,
            tracking_enabled,
        )
        if device is None or device.id is None:
            raise ReadingDeviceNotFoundError("Device was not found.")
        return SamplingSettingsDto(
            device_id=device.id,
            sampling_interval_seconds=device.sampling_interval_seconds,
            tracking_enabled=device.tracking_enabled,
        )

    def _get_device(self, device_id: UUID) -> Device:
        device = self.repository.get_device(device_id)
        if device is None:
            raise ReadingDeviceNotFoundError("Device was not found.")
        return device
