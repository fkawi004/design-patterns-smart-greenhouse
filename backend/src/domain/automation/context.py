from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class LocationAutomationContext:
    location_id: UUID
    zone_id: UUID
    zone_name: str
    latest_moisture: float | None
    moisture_threshold_low: float
    moisture_threshold_high: float
    latest_light: float | None = None
