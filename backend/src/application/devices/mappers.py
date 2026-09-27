from src.application.devices.dto import DeviceDto
from src.domain.devices.entity import Device


def device_to_dto(device: Device) -> DeviceDto:
    if device.id is None:
        raise ValueError("A persisted device must have an id")
    return DeviceDto(
        id=device.id,
        device_type=device.device_type,
        role=device.role,
        device_family=device.device_family,
        display_name=device.display_name,
        default_config=device.default_config,
    )
