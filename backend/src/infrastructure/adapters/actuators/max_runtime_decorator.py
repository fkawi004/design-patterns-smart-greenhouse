from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol
from uuid import UUID

from src.domain.actuators.ports import ActuatorPolicyError, ActuatorPort
from src.domain.actuators.state import ActuatorStateSnapshot


class ActuatorStateReader(Protocol):
    def get_snapshot(self, device_id: UUID) -> ActuatorStateSnapshot | None: ...


class MaxRunTimeExceededError(ActuatorPolicyError):
    def __init__(self) -> None:
        super().__init__("Max run time exceeded", ("maxRunTime",))


def utc_now() -> datetime:
    return datetime.now(UTC)


class MaxRunTimeActuatorDecorator(ActuatorPort):
    def __init__(
        self,
        inner: ActuatorPort,
        state_reader: ActuatorStateReader,
        clock: Callable[[], datetime] = utc_now,
        maximum_run_time: timedelta = timedelta(minutes=30),
    ) -> None:
        self.inner = inner
        self.state_reader = state_reader
        self.clock = clock
        self.maximum_run_time = maximum_run_time

    def apply(self, device_id: UUID, command: str, payload: dict[str, Any]) -> None:
        snapshot = self.state_reader.get_snapshot(device_id)
        if (
            snapshot is not None
            and snapshot.state == "running"
            and self.clock() - snapshot.updated_at >= self.maximum_run_time
        ):
            raise MaxRunTimeExceededError()
        self.inner.apply(device_id, command, payload)
