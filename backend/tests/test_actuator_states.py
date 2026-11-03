import pytest

from src.domain.actuators.context import ActuatorContext
from src.domain.actuators.state import IllegalTransitionError


def test_idle_to_running_allowed() -> None:
    actuator = ActuatorContext("idle")

    actuator.transition("running")

    assert actuator.state == "running"
    assert actuator.allowed_commands == ["stop", "report_error", "power_off"]


def test_running_to_maintenance_rejected() -> None:
    actuator = ActuatorContext("running")

    with pytest.raises(IllegalTransitionError):
        actuator.transition("maintenance")

    assert actuator.state == "running"
