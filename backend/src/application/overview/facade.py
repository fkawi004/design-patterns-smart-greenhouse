from typing import Protocol
from uuid import UUID

from src.application.automation.service import AutomationService
from src.application.overview.dto import (
    DeviceCountsDto,
    LastRecommendationDto,
    LatestReadingSummaryDto,
    LocationOverviewDto,
    OverviewDeviceDto,
    OverviewLocationDto,
    OverviewZoneDto,
)
from src.application.overview.errors import OverviewLocationNotFoundError
from src.domain.devices.entity import Device
from src.domain.locations.entity import Location
from src.domain.sensors.reading import Reading


class OverviewRepository(Protocol):
    def get_location_with_zones(self, location_id: UUID) -> Location | None: ...

    def list_assigned_devices(self, location_id: UUID) -> list[Device]: ...

    def latest_readings(self, device_ids: list[UUID]) -> dict[UUID, Reading]: ...


class StrategyKeyRepository(Protocol):
    def get_strategy_key(self, location_id: UUID) -> str | None: ...


class LocationOverviewFacade:
    def __init__(
        self,
        overview_repository: OverviewRepository,
        strategy_repository: StrategyKeyRepository,
        automation_service: AutomationService,
    ) -> None:
        self.overview_repository = overview_repository
        self.strategy_repository = strategy_repository
        self.automation_service = automation_service

    def get_overview(self, location_id: UUID) -> LocationOverviewDto:
        location = self.overview_repository.get_location_with_zones(location_id)
        if location is None or location.id is None:
            raise OverviewLocationNotFoundError("Location was not found.")

        devices = self.overview_repository.list_assigned_devices(location_id)
        device_ids = [device.id for device in devices if device.id is not None]
        readings = self.overview_repository.latest_readings(device_ids)
        devices_by_zone: dict[UUID, list[Device]] = {}
        for device in devices:
            if device.zone_id is not None:
                devices_by_zone.setdefault(device.zone_id, []).append(device)

        zones: list[OverviewZoneDto] = []
        for zone in location.zones:
            if zone.id is None:
                continue
            zone_devices = devices_by_zone.get(zone.id, [])
            zones.append(
                OverviewZoneDto(
                    id=zone.id,
                    name=zone.name,
                    moisture_threshold_low=zone.moisture_threshold_low,
                    moisture_threshold_high=zone.moisture_threshold_high,
                    devices=[self._device_dto(device) for device in zone_devices],
                    latest_readings=[
                        self._reading_dto(readings[device.id], device)
                        for device in zone_devices
                        if device.id is not None and device.id in readings
                    ],
                )
            )

        strategy_key = self.strategy_repository.get_strategy_key(location_id)
        last_recommendation = None
        if strategy_key is not None:
            recommendation = self.automation_service.evaluate(location_id)
            last_recommendation = LastRecommendationDto(
                action=recommendation.action,
                reason=recommendation.reason,
            )

        return LocationOverviewDto(
            location=OverviewLocationDto(id=location.id, name=location.name),
            device_counts=DeviceCountsDto(
                sensor=sum(device.role == "sensor" for device in devices),
                actuator=sum(device.role == "actuator" for device in devices),
            ),
            zones=zones,
            strategy_key=strategy_key,
            last_recommendation=last_recommendation,
        )

    @staticmethod
    def _device_dto(device: Device) -> OverviewDeviceDto:
        if device.id is None:
            raise ValueError("Overview devices must be persisted.")
        return OverviewDeviceDto(
            id=device.id,
            device_type=device.device_type,
            role=device.role,
            display_name=device.display_name,
        )

    @staticmethod
    def _reading_dto(reading: Reading, device: Device) -> LatestReadingSummaryDto:
        return LatestReadingSummaryDto(
            device_id=reading.device_id,
            value=reading.value,
            unit=reading.unit,
            recorded_at=reading.recorded_at,
            tracking_enabled=device.tracking_enabled,
            sampling_interval_seconds=device.sampling_interval_seconds,
        )
