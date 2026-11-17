from typing import Protocol

from src.application.actuators.dto import ActuatorExecutionDto
from src.domain.actuators.execution import ActuatorExecution


class ExecutionLogReader(Protocol):
    def list_recent(self, limit: int) -> list[ActuatorExecution]: ...


class ActuatorExecutionService:
    def __init__(self, log_reader: ExecutionLogReader) -> None:
        self.log_reader = log_reader

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
