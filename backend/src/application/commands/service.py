from typing import Any, Protocol
from uuid import UUID

from src.application.commands.dto import CommandLogDto
from src.application.devices.errors import ActuatorNotFoundError
from src.domain.actuators.context import ActuatorContext
from src.domain.actuators.ports import ActuatorPort
from src.domain.actuators.state import ActuatorStateSnapshot
from src.domain.commands.base import Command
from src.domain.commands.history import CommandLogEntry, CommandStatus
from src.domain.commands.invoker import CommandInvoker


class ActuatorStateRepository(Protocol):
    def get_snapshot(self, device_id: UUID) -> ActuatorStateSnapshot | None: ...

    def save_state(self, device_id: UUID, state: str) -> None: ...


class CommandLogRepository(Protocol):
    def record(
        self,
        command_type: str,
        device_id: UUID,
        payload: dict[str, Any],
        status: CommandStatus,
        error_message: str | None,
    ) -> CommandLogEntry: ...

    def list_recent(self, limit: int) -> list[CommandLogEntry]: ...


class CommandService:
    def __init__(
        self,
        invoker: CommandInvoker,
        actuator_port: ActuatorPort,
        state_repository: ActuatorStateRepository,
        log_repository: CommandLogRepository,
    ) -> None:
        self.invoker = invoker
        self.actuator_port = actuator_port
        self.state_repository = state_repository
        self.log_repository = log_repository

    def execute(
        self,
        command_type: str,
        device_id: UUID,
        payload: dict[str, Any],
    ) -> CommandLogDto:
        command = self.invoker.create(command_type, device_id, payload)
        snapshot = self.state_repository.get_snapshot(device_id)
        if snapshot is None:
            raise ActuatorNotFoundError("Actuator was not found.")

        context = ActuatorContext(snapshot.state)
        if command.command_type not in context.allowed_commands:
            return self._record(
                command,
                status="rejected",
                error_message=(
                    f"Command '{command.command_type}' is not allowed while the actuator "
                    f"is '{context.state}'."
                ),
            )

        try:
            self.invoker.run(command, self.actuator_port)
            if command.target_state is not None and command.target_state != context.state:
                context.transition(command.target_state)
                self.state_repository.save_state(device_id, context.state)
        except Exception as error:
            return self._record(command, status="failed", error_message=str(error))

        return self._record(command, status="success", error_message=None)

    def list_history(self, limit: int) -> list[CommandLogDto]:
        return [self._to_dto(entry) for entry in self.log_repository.list_recent(limit)]

    def _record(
        self,
        command: Command,
        status: CommandStatus,
        error_message: str | None,
    ) -> CommandLogDto:
        entry = self.log_repository.record(
            command_type=command.command_type,
            device_id=command.device_id,
            payload=command.payload,
            status=status,
            error_message=error_message,
        )
        return self._to_dto(entry)

    @staticmethod
    def _to_dto(entry: CommandLogEntry) -> CommandLogDto:
        return CommandLogDto(
            id=entry.id,
            command_type=entry.command_type,
            device_id=entry.device_id,
            payload=entry.payload,
            status=entry.status,
            error_message=entry.error_message,
            created_at=entry.created_at,
        )
