from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest

from src.domain.actuators.ports import ActuatorPort
from src.domain.actuators.state import ActuatorStateSnapshot
from src.infrastructure.adapters.actuators.logging_decorator import (
    LoggingActuatorDecorator,
)
from src.infrastructure.adapters.actuators.max_runtime_decorator import (
    MaxRunTimeActuatorDecorator,
    MaxRunTimeExceededError,
)


class SpyActuator(ActuatorPort):
    def __init__(self) -> None:
        self.calls: list[tuple[UUID, str, dict[str, Any]]] = []

    def apply(self, device_id: UUID, command: str, payload: dict[str, Any]) -> None:
        self.calls.append((device_id, command, payload))


@dataclass
class StubStateReader:
    snapshot: ActuatorStateSnapshot | None

    def get_snapshot(self, _device_id: UUID) -> ActuatorStateSnapshot | None:
        return self.snapshot


class MemoryLogWriter:
    def __init__(self) -> None:
        self.rows: list[dict[str, object]] = []

    def record(
        self,
        device_id: UUID,
        success: bool,
        policy_applied: list[str],
        message: str | None,
    ) -> object:
        row = {
            "device_id": device_id,
            "success": success,
            "policy_applied": policy_applied,
            "message": message,
        }
        self.rows.append(row)
        return row


def test_max_runtime_does_not_call_inner() -> None:
    now = datetime(2026, 11, 10, 12, 0, tzinfo=UTC)
    inner = SpyActuator()
    decorator = MaxRunTimeActuatorDecorator(
        inner,
        StubStateReader(
            ActuatorStateSnapshot(
                state="running",
                updated_at=now - timedelta(minutes=30),
            )
        ),
        clock=lambda: now,
    )

    with pytest.raises(MaxRunTimeExceededError):
        decorator.apply(uuid4(), "anything", {})

    assert inner.calls == []


def test_max_runtime_forwards_when_policy_allows() -> None:
    now = datetime(2026, 11, 10, 12, 0, tzinfo=UTC)
    device_id = uuid4()
    inner = SpyActuator()
    decorator = MaxRunTimeActuatorDecorator(
        inner,
        StubStateReader(
            ActuatorStateSnapshot(
                state="idle",
                updated_at=now - timedelta(hours=2),
            )
        ),
        clock=lambda: now,
    )

    decorator.apply(device_id, "unknown_command", {"level": 2})

    assert inner.calls == [(device_id, "unknown_command", {"level": 2})]


def test_logging_records_success() -> None:
    device_id = uuid4()
    writer = MemoryLogWriter()
    decorator = LoggingActuatorDecorator(SpyActuator(), writer)

    decorator.apply(device_id, "unknown_command", {})

    assert writer.rows == [
        {
            "device_id": device_id,
            "success": True,
            "policy_applied": ["logging"],
            "message": None,
        }
    ]


def test_failed_policy_is_always_logged() -> None:
    now = datetime(2026, 11, 10, 12, 0, tzinfo=UTC)
    device_id = uuid4()
    writer = MemoryLogWriter()
    guarded = MaxRunTimeActuatorDecorator(
        SpyActuator(),
        StubStateReader(
            ActuatorStateSnapshot(
                state="running",
                updated_at=now - timedelta(minutes=31),
            )
        ),
        clock=lambda: now,
    )
    decorator = LoggingActuatorDecorator(guarded, writer)

    with pytest.raises(MaxRunTimeExceededError):
        decorator.apply(device_id, "anything", {})

    assert writer.rows == [
        {
            "device_id": device_id,
            "success": False,
            "policy_applied": ["maxRunTime", "logging"],
            "message": "Max run time exceeded",
        }
    ]
