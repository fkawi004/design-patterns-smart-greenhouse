from dataclasses import dataclass, field
from typing import Any, ClassVar
from uuid import UUID

from src.domain.actuators.ports import ActuatorPort
from src.domain.commands.base import Command


@dataclass(frozen=True, slots=True)
class StartPumpCommand(Command):
    device_id: UUID
    payload: dict[str, Any] = field(default_factory=dict)
    command_type: ClassVar[str] = "start_pump"
    target_state: ClassVar[str] = "running"

    def execute(self, port: ActuatorPort) -> None:
        port.apply(self.device_id, self.command_type, self.payload)


@dataclass(frozen=True, slots=True)
class StopPumpCommand(Command):
    device_id: UUID
    payload: dict[str, Any] = field(default_factory=dict)
    command_type: ClassVar[str] = "stop_pump"
    target_state: ClassVar[str] = "idle"

    def execute(self, port: ActuatorPort) -> None:
        port.apply(self.device_id, self.command_type, self.payload)
