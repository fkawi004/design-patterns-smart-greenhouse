import random
from datetime import UTC, datetime

from src.domain.devices.entity import Device
from src.domain.sensors.ports import SensorPort
from src.domain.sensors.reading import Reading
from src.infrastructure.adapters.sensors.errors import SensorAdapterError


class SimulationSensorAdapter(SensorPort):
    def read(self, device: Device, recorded_at: datetime | None = None) -> Reading:
        if device.id is None:
            raise SensorAdapterError("A sensor must be persisted before it can be read.")
        if device.device_type == "moisture_sensor":
            value, unit = random.uniform(0.2, 0.6), "vwc"
        elif device.device_type == "light_sensor":
            value, unit = random.uniform(200.0, 2000.0), "lux"
        else:
            raise SensorAdapterError(f"Unsupported simulation sensor '{device.device_type}'.")
        return Reading(
            device_id=device.id,
            value=round(value, 4),
            unit=unit,
            source="simulation",
            recorded_at=recorded_at or datetime.now(UTC),
        )
