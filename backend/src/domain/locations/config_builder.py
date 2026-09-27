from typing import Any

from src.domain.locations.entity import Location, LocationConfig, Zone
from src.domain.locations.errors import ConfigurationError


def validate_zone(
    name: str,
    moisture_threshold_low: float,
    moisture_threshold_high: float,
) -> None:
    if not name.strip():
        raise ConfigurationError("Zone name is required.")
    if not 0.0 <= moisture_threshold_low <= 1.0:
        raise ConfigurationError("Low moisture threshold must be between 0.0 and 1.0.")
    if not 0.0 <= moisture_threshold_high <= 1.0:
        raise ConfigurationError("High moisture threshold must be between 0.0 and 1.0.")
    if moisture_threshold_low >= moisture_threshold_high:
        raise ConfigurationError("Low moisture threshold must be less than high threshold.")


class LocationConfigBuilder:
    def __init__(self) -> None:
        self._location_name = ""
        self._zones: list[Zone] = []

    def with_location_name(self, name: str) -> "LocationConfigBuilder":
        self._location_name = name
        return self

    def add_zone(
        self,
        name: str,
        moisture_threshold_low: float,
        moisture_threshold_high: float,
        schedule: dict[str, Any] | None = None,
    ) -> "LocationConfigBuilder":
        self._zones.append(
            Zone(
                name=name,
                moisture_threshold_low=moisture_threshold_low,
                moisture_threshold_high=moisture_threshold_high,
                schedule=dict(schedule or {}),
            )
        )
        return self

    def build(self) -> LocationConfig:
        location_name = self._location_name.strip()
        if not location_name:
            raise ConfigurationError("Location name is required.")
        if not self._zones:
            raise ConfigurationError("At least one zone is required.")

        normalized_names: set[str] = set()
        validated_zones: list[Zone] = []
        for zone in self._zones:
            validate_zone(
                zone.name,
                zone.moisture_threshold_low,
                zone.moisture_threshold_high,
            )
            normalized_name = zone.name.strip().casefold()
            if normalized_name in normalized_names:
                raise ConfigurationError("Zone names must be unique within a location.")
            normalized_names.add(normalized_name)
            validated_zones.append(
                Zone(
                    name=zone.name.strip(),
                    moisture_threshold_low=zone.moisture_threshold_low,
                    moisture_threshold_high=zone.moisture_threshold_high,
                    schedule=dict(zone.schedule),
                )
            )

        return LocationConfig(location=Location(name=location_name, zones=tuple(validated_zones)))
