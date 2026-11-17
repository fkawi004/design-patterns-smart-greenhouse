from typing import Any
from uuid import UUID, uuid4

import pytest

from src.domain.actuators.ports import ActuatorPort
from src.domain.commands.base import UnknownCommandTypeError
from src.domain.commands.invoker import CommandInvoker


class RecordingActuatorPort(ActuatorPort):
    def __init__(self) -> None:
        self.calls: list[tuple[UUID, str, dict[str, Any]]] = []

    def apply(self, device_id: UUID, command: str, payload: dict[str, Any]) -> None:
        self.calls.append((device_id, command, payload))


@pytest.mark.parametrize(
    ("command_type", "target_state", "payload"),
    [
        ("start_pump", "running", {}),
        ("stop_pump", "idle", {}),
        ("set_light_level", "running", {"level": 42}),
    ],
)
def test_invoker_creates_and_runs_registered_commands(
    command_type: str,
    target_state: str,
    payload: dict[str, Any],
) -> None:
    device_id = uuid4()
    port = RecordingActuatorPort()
    invoker = CommandInvoker()

    command = invoker.create(command_type, device_id, payload)
    invoker.run(command, port)

    assert command.command_type == command_type
    assert command.target_state == target_state
    assert port.calls == [(device_id, command_type, payload)]


def test_unknown_command_type_is_rejected_before_execution() -> None:
    invoker = CommandInvoker()

    with pytest.raises(UnknownCommandTypeError):
        invoker.create("open_portal", uuid4(), {})
