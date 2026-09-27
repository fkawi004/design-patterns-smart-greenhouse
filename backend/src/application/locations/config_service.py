from typing import Protocol
from uuid import UUID

from src.application.locations.dto import (
    BuildLocationConfigRequestDto,
    LocationConfigDto,
    LocationSummaryDto,
    ZoneDto,
    ZoneWriteDto,
)
from src.application.locations.errors import (
    LastZoneDeletionError,
    LocationNotFoundError,
    ZoneNotFoundError,
)
from src.application.locations.mappers import (
    location_config_to_dto,
    location_summary_to_dto,
    zone_to_dto,
)
from src.domain.locations.config_builder import LocationConfigBuilder, validate_zone
from src.domain.locations.entity import Location, LocationConfig, Zone
from src.domain.locations.errors import ConfigurationError


class LocationRepository(Protocol):
    def save_config(self, config: LocationConfig) -> Location: ...

    def get_config(self, location_id: UUID) -> Location | None: ...

    def list_locations(self) -> list[Location]: ...

    def delete_location(self, location_id: UUID) -> bool: ...

    def add_zone(self, location_id: UUID, zone: Zone) -> Zone | None: ...

    def update_zone(self, location_id: UUID, zone_id: UUID, zone: Zone) -> Zone | None: ...

    def delete_zone(self, location_id: UUID, zone_id: UUID) -> bool: ...


class LocationConfigService:
    def __init__(self, repository: LocationRepository) -> None:
        self.repository = repository

    def build_and_save(self, request: BuildLocationConfigRequestDto) -> LocationConfigDto:
        builder = LocationConfigBuilder().with_location_name(request.location_name)
        for zone in request.zones:
            builder.add_zone(
                zone.name,
                zone.moisture_threshold_low,
                zone.moisture_threshold_high,
                zone.schedule,
            )
        return location_config_to_dto(self.repository.save_config(builder.build()))

    def get_config(self, location_id: UUID) -> LocationConfigDto:
        location = self.repository.get_config(location_id)
        if location is None:
            raise LocationNotFoundError("Location was not found.")
        return location_config_to_dto(location)

    def list_locations(self) -> list[LocationSummaryDto]:
        return [location_summary_to_dto(item) for item in self.repository.list_locations()]

    def delete_location(self, location_id: UUID) -> None:
        if not self.repository.delete_location(location_id):
            raise LocationNotFoundError("Location was not found.")

    def add_zone(self, location_id: UUID, request: ZoneWriteDto) -> ZoneDto:
        current = self._get_location(location_id)
        self._validate_zone_request(request)
        self._require_unique_zone_name(current, request.name)
        zone = self.repository.add_zone(location_id, self._zone_from_request(request))
        if zone is None:
            raise LocationNotFoundError("Location was not found.")
        return zone_to_dto(zone)

    def update_zone(
        self,
        location_id: UUID,
        zone_id: UUID,
        request: ZoneWriteDto,
    ) -> ZoneDto:
        current = self._get_location(location_id)
        if not any(zone.id == zone_id for zone in current.zones):
            raise ZoneNotFoundError("Zone was not found in this location.")
        self._validate_zone_request(request)
        self._require_unique_zone_name(current, request.name, except_zone_id=zone_id)
        zone = self.repository.update_zone(
            location_id,
            zone_id,
            self._zone_from_request(request),
        )
        if zone is None:
            raise ZoneNotFoundError("Zone was not found in this location.")
        return zone_to_dto(zone)

    def delete_zone(self, location_id: UUID, zone_id: UUID) -> None:
        current = self._get_location(location_id)
        if not any(zone.id == zone_id for zone in current.zones):
            raise ZoneNotFoundError("Zone was not found in this location.")
        if len(current.zones) == 1:
            raise LastZoneDeletionError("A location must keep at least one zone.")
        if not self.repository.delete_zone(location_id, zone_id):
            raise ZoneNotFoundError("Zone was not found in this location.")

    def _get_location(self, location_id: UUID) -> Location:
        location = self.repository.get_config(location_id)
        if location is None:
            raise LocationNotFoundError("Location was not found.")
        return location

    @staticmethod
    def _validate_zone_request(request: ZoneWriteDto) -> None:
        validate_zone(
            request.name,
            request.moisture_threshold_low,
            request.moisture_threshold_high,
        )

    @staticmethod
    def _require_unique_zone_name(
        location: Location,
        name: str,
        except_zone_id: UUID | None = None,
    ) -> None:
        normalized = name.strip().casefold()
        if any(
            zone.name.casefold() == normalized and zone.id != except_zone_id
            for zone in location.zones
        ):
            raise ConfigurationError("Zone names must be unique within a location.")

    @staticmethod
    def _zone_from_request(request: ZoneWriteDto) -> Zone:
        return Zone(
            name=request.name.strip(),
            moisture_threshold_low=request.moisture_threshold_low,
            moisture_threshold_high=request.moisture_threshold_high,
            schedule=dict(request.schedule),
        )
