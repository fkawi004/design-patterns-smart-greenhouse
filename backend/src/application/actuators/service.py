from typing import Protocol
from uuid import UUID

from src.application.actuators.dto import ActuatorExecutionDto
from src.application.devices.errors import ActuatorNotFoundError
from src.domain.actuators.execution import ActuatorExecution
from src.domain.actuators.ports import ActuatorPort
from src.domain.actuators.state import ActuatorStateSnapshot


class ActuatorStateReader(Protocol):
    def get_snapshot(self, device_id: UUID) -> ActuatorStateSnapshot | None: ...


class ExecutionLogReader(Protocol):
    def list_recent(self, limit: int) -> list[ActuatorExecution]: ...


class ActuatorExecutionService:
    def __init__(
        self,
        decorated_port: ActuatorPort,
        state_reader: ActuatorStateReader,
        log_reader: ExecutionLogReader,
    ) -> None:
        self.decorated_port = decorated_port
        self.state_reader = state_reader
        self.log_reader = log_reader

    def apply(self, device_id: UUID, command: str, payload: dict) -> None:
        if self.state_reader.get_snapshot(device_id) is None:
            raise ActuatorNotFoundError("Actuator was not found.")
        self.decorated_port.apply(device_id, command, payload)

    def list_executions(self, limit: int) -> list[ActuatorExecutionDto]:
        return [self._to_dto(item) for item in self.log_reader.list_recent(limit)]

    @staticmethod
    def _to_dto(item: ActuatorExecution) -> ActuatorExecutionDto:
        return ActuatorExecutionDto(
            id=item.id,
            device_id=item.device_id,
            success=item.success,
            policy_applied=list(item.policy_applied),
            message=item.message,
            created_at=item.created_at,
        )
