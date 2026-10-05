from abc import ABC, abstractmethod
from datetime import datetime

from src.domain.devices.entity import Device
from src.domain.sensors.reading import Reading


class SensorPort(ABC):
    @abstractmethod
    def read(self, device: Device, recorded_at: datetime | None = None) -> Reading:
        """Read one device and return the normalized domain value."""
