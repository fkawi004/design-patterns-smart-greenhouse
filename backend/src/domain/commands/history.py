from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

CommandStatus = Literal["success", "failed", "rejected"]


@dataclass(frozen=True, slots=True)
class CommandLogEntry:
    id: UUID
    command_type: str
    device_id: UUID
    payload: dict[str, Any]
    status: CommandStatus
    error_message: str | None
    created_at: datetime
