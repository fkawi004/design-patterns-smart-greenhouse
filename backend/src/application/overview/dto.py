from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class OverviewLocationDto(BaseModel):
    id: UUID
    name: str


class DeviceCountsDto(BaseModel):
    sensor: int
    actuator: int


class OverviewDeviceDto(BaseModel):
    id: UUID
    device_type: str
    role: Literal["sensor", "actuator"]
    display_name: str


class LatestReadingSummaryDto(BaseModel):
    device_id: UUID
    value: float
    unit: str
    recorded_at: datetime
    tracking_enabled: bool
    sampling_interval_seconds: int


class OverviewZoneDto(BaseModel):
    id: UUID
    name: str
    moisture_threshold_low: float
    moisture_threshold_high: float
    devices: list[OverviewDeviceDto]
    latest_readings: list[LatestReadingSummaryDto]


class LastRecommendationDto(BaseModel):
    action: str
    reason: str


class LocationOverviewDto(BaseModel):
    location: OverviewLocationDto
    device_counts: DeviceCountsDto
    zones: list[OverviewZoneDto]
    strategy_key: str | None
    last_recommendation: LastRecommendationDto | None
