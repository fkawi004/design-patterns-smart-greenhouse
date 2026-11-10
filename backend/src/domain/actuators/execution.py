from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ActuatorExecution:
    id: UUID
    device_id: UUID
    success: bool
    policy_applied: tuple[str, ...]
    message: str | None
    created_at: datetime
