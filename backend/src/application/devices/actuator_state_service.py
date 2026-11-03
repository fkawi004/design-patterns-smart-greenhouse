from typing import Protocol
from uuid import UUID

from src.application.devices.dto import ActuatorStateDto
from src.application.devices.errors import ActuatorNotFoundError
from src.domain.actuators.context import ActuatorContext


class ActuatorStateRepository(Protocol):
    def get_state(self, device_id: UUID) -> str | None: ...

    def save_state(self, device_id: UUID, state: str) -> None: ...


class ActuatorStateService:
    def __init__(self, repository: ActuatorStateRepository) -> None:
        self.repository = repository

    def transition(self, device_id: UUID, target: str) -> ActuatorStateDto:
        current_state = self.repository.get_state(device_id)
        if current_state is None:
            raise ActuatorNotFoundError("Actuator was not found.")

        context = ActuatorContext(current_state)
        context.transition(target)
        self.repository.save_state(device_id, context.state)
        return ActuatorStateDto(
            device_id=device_id,
            state=context.state,
            allowed_commands=context.allowed_commands,
        )
