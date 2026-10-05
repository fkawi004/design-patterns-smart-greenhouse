from datetime import UTC, datetime
from typing import Any

from src.domain.devices.entity import Device
from src.domain.sensors.ports import SensorPort
from src.domain.sensors.reading import Reading
from src.infrastructure.adapters.sensors.errors import SensorAdapterError


class MqttSensorAdapter(SensorPort):
    def read(self, device: Device, recorded_at: datetime | None = None) -> Reading:
        raise SensorAdapterError(
            "MQTT sensors require an inbound payload; no broker transport runs in Phase 5."
        )

    def translate(
        self,
        device: Device,
        payload: dict[str, Any],
        recorded_at: datetime | None = None,
    ) -> Reading:
        if device.id is None:
            raise SensorAdapterError("A sensor must be persisted before it can be read.")
        try:
            value = float(payload["value"])
            unit = str(payload["unit"])
        except (KeyError, TypeError, ValueError) as error:
            raise SensorAdapterError("MQTT payload must contain numeric value and unit.") from error
        if not unit.strip():
            raise SensorAdapterError("MQTT payload unit is required.")
        return Reading(
            device_id=device.id,
            value=value,
            unit=unit,
            source="mqtt",
            recorded_at=recorded_at or datetime.now(UTC),
        )
