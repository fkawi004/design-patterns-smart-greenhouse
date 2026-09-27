from typing import Protocol
from uuid import UUID

from src.application.devices.dto import DeviceDto
from src.application.devices.mappers import device_to_dto
from src.application.locations.errors import (
    DeviceNotFoundError,
    ZoneNotFoundError,
)
from src.domain.devices.entity import Device
from src.domain.locations.entity import Zone


class ZoneAssignmentRepository(Protocol):
    def get_device(self, device_id: UUID) -> Device | None: ...

    def get_zone(self, zone_id: UUID) -> Zone | None: ...

    def save_assignment(self, device_id: UUID, zone: Zone | None) -> Device: ...

    def list_zone_devices(self, location_id: UUID, zone_id: UUID) -> list[Device] | None: ...


class ZoneAssignmentService:
    def __init__(self, repository: ZoneAssignmentRepository) -> None:
        self.repository = repository

    def assign(self, device_id: UUID, zone_id: UUID | None) -> DeviceDto:
        if self.repository.get_device(device_id) is None:
            raise DeviceNotFoundError("Device was not found.")
        zone = None
        if zone_id is not None:
            zone = self.repository.get_zone(zone_id)
            if zone is None:
                raise ZoneNotFoundError("Zone was not found.")
        return device_to_dto(self.repository.save_assignment(device_id, zone))

    def list_devices(self, location_id: UUID, zone_id: UUID) -> list[DeviceDto]:
        devices = self.repository.list_zone_devices(location_id, zone_id)
        if devices is None:
            raise ZoneNotFoundError("Zone was not found in this location.")
        return [device_to_dto(device) for device in devices]
