from dataclasses import dataclass
from typing import Any
from uuid import UUID

from src.domain.actuators.ports import ActuatorPort


@dataclass(frozen=True, slots=True)
class AppliedCommand:
    device_id: UUID
    command: str
    payload: dict[str, Any]


class SimulationActuatorAdapter(ActuatorPort):
    def __init__(self) -> None:
        self.applied_commands: list[AppliedCommand] = []

    def apply(self, device_id: UUID, command: str, payload: dict[str, Any]) -> None:
        self.applied_commands.append(
            AppliedCommand(device_id=device_id, command=command, payload=dict(payload))
        )
