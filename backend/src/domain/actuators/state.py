from abc import ABC
from dataclasses import dataclass
from datetime import datetime


class IllegalTransitionError(ValueError):
    """Raised when an actuator cannot move to the requested lifecycle state."""


@dataclass(frozen=True, slots=True)
class ActuatorStateSnapshot:
    state: str
    updated_at: datetime


class ActuatorState(ABC):
    name: str
    allowed_targets: frozenset[str]
    commands: tuple[str, ...]

    def allows(self, target: str) -> bool:
        return target in self.allowed_targets

    def allowed_commands(self) -> list[str]:
        return list(self.commands)


class OffState(ActuatorState):
    name = "off"
    allowed_targets = frozenset({"idle", "error"})
    commands = ("power_on", "report_error")


class IdleState(ActuatorState):
    name = "idle"
    allowed_targets = frozenset({"running", "maintenance", "error", "off"})
    commands = ("start", "enter_maintenance", "report_error", "power_off")


class RunningState(ActuatorState):
    name = "running"
    allowed_targets = frozenset({"idle", "error", "off"})
    commands = ("stop", "report_error", "power_off")


class ErrorState(ActuatorState):
    name = "error"
    allowed_targets = frozenset({"idle", "maintenance", "off"})
    commands = ("reset", "enter_maintenance", "power_off")


class MaintenanceState(ActuatorState):
    name = "maintenance"
    allowed_targets = frozenset({"idle", "error", "off"})
    commands = ("finish_maintenance", "report_error", "power_off")


STATE_BY_NAME: dict[str, ActuatorState] = {
    state.name: state
    for state in (
        OffState(),
        IdleState(),
        RunningState(),
        ErrorState(),
        MaintenanceState(),
    )
}


def actuator_state(name: str) -> ActuatorState:
    try:
        return STATE_BY_NAME[name]
    except KeyError as error:
        raise IllegalTransitionError(f"Unknown actuator state '{name}'.") from error
