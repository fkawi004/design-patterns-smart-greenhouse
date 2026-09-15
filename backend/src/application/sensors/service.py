from typing import Protocol

from src.domain.sensors.creators import get_sensor_creator
from src.domain.sensors.entity import Sensor


class SensorRepository(Protocol):
    def save(self, sensor: Sensor) -> Sensor: ...

    def list_sensors(self) -> list[Sensor]: ...


class SensorService:
    def __init__(self, repository: SensorRepository) -> None:
        self.repository = repository

    def create_sensor(self, type_key: str, display_name: str | None = None) -> Sensor:
        creator = get_sensor_creator(type_key)
        sensor = creator.create_sensor(display_name)
        return self.repository.save(sensor)

    def list_sensors(self) -> list[Sensor]:
        return self.repository.list_sensors()
