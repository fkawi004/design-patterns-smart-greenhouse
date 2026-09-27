from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Zone:
    name: str
    moisture_threshold_low: float
    moisture_threshold_high: float
    schedule: dict[str, Any] = field(default_factory=dict)
    id: UUID | None = None
    location_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class Location:
    name: str
    zones: tuple[Zone, ...]
    id: UUID | None = None


@dataclass(frozen=True, slots=True)
class LocationConfig:
    location: Location
