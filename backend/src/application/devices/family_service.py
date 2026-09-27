from typing import Protocol

from src.domain.devices.entity import Device
from src.domain.devices.family_factory import get_device_family_factory


class DeviceRepository(Protocol):
    def save_many(self, devices: list[Device]) -> list[Device]: ...

    def list_devices(
        self,
        device_family: str | None = None,
        role: str | None = None,
    ) -> list[Device]: ...


class DeviceFamilyService:
    def __init__(self, repository: DeviceRepository) -> None:
        self.repository = repository

    def provision_family(self, family: str) -> list[Device]:
        factory = get_device_family_factory(family)
        return self.repository.save_many(factory.create_device_set())

    def list_devices(
        self,
        family: str | None = None,
        role: str | None = None,
    ) -> list[Device]:
        return self.repository.list_devices(device_family=family, role=role)
