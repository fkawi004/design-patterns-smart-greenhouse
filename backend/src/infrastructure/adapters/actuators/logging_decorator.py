from typing import Any, Protocol
from uuid import UUID

from src.domain.actuators.ports import ActuatorPolicyError, ActuatorPort


class ExecutionLogWriter(Protocol):
    def record(
        self,
        device_id: UUID,
        success: bool,
        policy_applied: list[str],
        message: str | None,
    ) -> object: ...


class LoggingActuatorDecorator(ActuatorPort):
    def __init__(self, inner: ActuatorPort, log_writer: ExecutionLogWriter) -> None:
        self.inner = inner
        self.log_writer = log_writer

    def apply(self, device_id: UUID, command: str, payload: dict[str, Any]) -> None:
        try:
            self.inner.apply(device_id, command, payload)
        except ActuatorPolicyError as error:
            self.log_writer.record(
                device_id=device_id,
                success=False,
                policy_applied=[*error.policy_applied, "logging"],
                message=str(error),
            )
            raise
        except Exception as error:
            self.log_writer.record(
                device_id=device_id,
                success=False,
                policy_applied=["logging"],
                message=str(error),
            )
            raise
        else:
            self.log_writer.record(
                device_id=device_id,
                success=True,
                policy_applied=["logging"],
                message=None,
            )
