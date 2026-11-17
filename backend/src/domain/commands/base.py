from abc import ABC, abstractmethod
from typing import Any, ClassVar
from uuid import UUID

from src.domain.actuators.ports import ActuatorPort


class Command(ABC):
    command_type: ClassVar[str]
    target_state: ClassVar[str | None]
    device_id: UUID
    payload: dict[str, Any]

    @abstractmethod
    def execute(self, port: ActuatorPort) -> None:
        """Send this request through the actuator port."""


class UnknownCommandTypeError(ValueError):
    pass
