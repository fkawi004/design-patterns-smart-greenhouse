from src.domain.actuators.state import (
    ActuatorState,
    IllegalTransitionError,
    actuator_state,
)


class ActuatorContext:
    def __init__(self, state: str) -> None:
        self._state = actuator_state(state)

    @property
    def state(self) -> str:
        return self._state.name

    @property
    def allowed_commands(self) -> list[str]:
        return self._state.allowed_commands()

    def transition(self, target: str) -> None:
        next_state: ActuatorState = actuator_state(target)
        if not self._state.allows(next_state.name):
            raise IllegalTransitionError(
                f"Actuator cannot transition from '{self.state}' to '{target}'."
            )
        self._state = next_state
