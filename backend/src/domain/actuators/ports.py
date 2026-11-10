from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


class ActuatorPort(ABC):
    @abstractmethod
    def apply(self, device_id: UUID, command: str, payload: dict[str, Any]) -> None:
        """Apply a normalized actuator command."""


class ActuatorPolicyError(RuntimeError):
    def __init__(self, message: str, policy_applied: tuple[str, ...]) -> None:
        super().__init__(message)
        self.policy_applied = policy_applied
