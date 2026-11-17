from collections.abc import Mapping
from typing import Any
from uuid import UUID

from src.domain.actuators.ports import ActuatorPort
from src.domain.commands.base import Command, UnknownCommandTypeError
from src.domain.commands.light import SetLightLevelCommand
from src.domain.commands.pump import StartPumpCommand, StopPumpCommand

CommandType = type[StartPumpCommand] | type[StopPumpCommand] | type[SetLightLevelCommand]

COMMAND_REGISTRY: dict[str, CommandType] = {
    command.command_type: command
    for command in (StartPumpCommand, StopPumpCommand, SetLightLevelCommand)
}


class CommandInvoker:
    def __init__(self, registry: Mapping[str, CommandType] = COMMAND_REGISTRY) -> None:
        self.registry = registry

    def create(
        self,
        command_type: str,
        device_id: UUID,
        payload: dict[str, Any],
    ) -> Command:
        try:
            command_class = self.registry[command_type]
        except KeyError as error:
            raise UnknownCommandTypeError(
                f"Unknown command type '{command_type}'."
            ) from error
        return command_class(device_id=device_id, payload=dict(payload))

    @staticmethod
    def run(command: Command, port: ActuatorPort) -> None:
        command.execute(port)
