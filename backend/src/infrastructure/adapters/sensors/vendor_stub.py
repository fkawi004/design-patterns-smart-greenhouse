from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from src.domain.devices.entity import Device
from src.domain.sensors.ports import SensorPort
from src.domain.sensors.reading import Reading
from src.infrastructure.adapters.sensors.errors import SensorAdapterError

VendorReader = Callable[[Device], dict[str, Any]]


class VendorStubSensorAdapter(SensorPort):
    def __init__(self, raw_reader: VendorReader | None = None) -> None:
        self.raw_reader = raw_reader or self._stub_payload

    def read(self, device: Device, recorded_at: datetime | None = None) -> Reading:
        return self.translate(device, self.raw_reader(device), recorded_at)

    def translate(
        self,
        device: Device,
        raw_payload: dict[str, Any],
        recorded_at: datetime | None = None,
    ) -> Reading:
        if device.id is None:
            raise SensorAdapterError("A sensor must be persisted before it can be read.")
        try:
            value = float(raw_payload["measurement"])
            unit = str(raw_payload["uom"])
        except (KeyError, TypeError, ValueError) as error:
            raise SensorAdapterError("Vendor payload must contain measurement and uom.") from error
        return Reading(
            device_id=device.id,
            value=value,
            unit=unit,
            source="vendor",
            recorded_at=recorded_at or datetime.now(UTC),
        )

    @staticmethod
    def _stub_payload(device: Device) -> dict[str, Any]:
        if device.device_type == "moisture_sensor":
            return {"measurement": 0.38, "uom": "vwc", "status_code": 200}
        if device.device_type == "light_sensor":
            return {"measurement": 900, "uom": "lux", "status_code": 200}
        raise SensorAdapterError(f"Unsupported vendor sensor '{device.device_type}'.")
