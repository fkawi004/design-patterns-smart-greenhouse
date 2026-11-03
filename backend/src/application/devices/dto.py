from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel


class DeviceDto(BaseModel):
    id: UUID
    device_type: str
    role: Literal["sensor", "actuator"]
    device_family: str
    display_name: str
    default_config: dict[str, Any]
    zone_id: UUID | None = None
    location_id: UUID | None = None
    sampling_interval_seconds: int
    tracking_enabled: bool
    state: str | None
    allowed_commands: list[str]


class ActuatorTransitionRequestDto(BaseModel):
    target: str


class ActuatorStateDto(BaseModel):
    device_id: UUID
    state: str
    allowed_commands: list[str]
