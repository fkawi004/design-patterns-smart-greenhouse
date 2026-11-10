from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ActuatorApplyRequestDto(BaseModel):
    command: str
    payload: dict[str, Any] = Field(default_factory=dict)


class ActuatorExecutionDto(BaseModel):
    id: UUID
    device_id: UUID
    success: bool
    policy_applied: list[str]
    message: str | None
    created_at: datetime
