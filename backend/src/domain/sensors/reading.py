from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Reading:
    device_id: UUID
    value: float
    unit: str
    source: str
    recorded_at: datetime

    def __post_init__(self) -> None:
        if self.recorded_at.tzinfo is None:
            raise ValueError("Reading timestamp must include a timezone.")
        if not self.unit.strip():
            raise ValueError("Reading unit is required.")
