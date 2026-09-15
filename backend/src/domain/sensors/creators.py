from abc import ABC, abstractmethod

from src.domain.sensors.entity import Sensor


class UnknownSensorTypeError(ValueError):
    pass


class SensorCreator(ABC):
    @abstractmethod
    def create_sensor(self, display_name: str | None = None) -> Sensor:
        """Create an unpersisted sensor with type-specific defaults."""


class MoistureSensorCreator(SensorCreator):
    def create_sensor(self, display_name: str | None = None) -> Sensor:
        return Sensor(
            device_type="moisture_sensor",
            display_name=display_name or "Moisture Sensor",
            default_config={
                "unit": "percent",
                "sampling_interval_seconds": 60,
                "moisture_threshold": 30,
            },
        )


class LightSensorCreator(SensorCreator):
    def create_sensor(self, display_name: str | None = None) -> Sensor:
        return Sensor(
            device_type="light_sensor",
            display_name=display_name or "Light Sensor",
            default_config={
                "unit": "lux",
                "sampling_interval_seconds": 30,
                "low_light_threshold": 200,
            },
        )


SENSOR_CREATORS: dict[str, SensorCreator] = {
    "moisture": MoistureSensorCreator(),
    "light": LightSensorCreator(),
}


def get_sensor_creator(type_key: str) -> SensorCreator:
    try:
        return SENSOR_CREATORS[type_key]
    except KeyError as error:
        supported = ", ".join(sorted(SENSOR_CREATORS))
        raise UnknownSensorTypeError(
            f"Unknown sensor type '{type_key}'. Supported types: {supported}."
        ) from error
