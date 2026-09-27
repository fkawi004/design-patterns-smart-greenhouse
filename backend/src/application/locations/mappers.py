from src.application.locations.dto import (
    LocationConfigDto,
    LocationSummaryDto,
    ZoneDto,
)
from src.domain.locations.entity import Location, Zone


def location_summary_to_dto(location: Location) -> LocationSummaryDto:
    if location.id is None:
        raise ValueError("A persisted location must have an id")
    return LocationSummaryDto(id=location.id, name=location.name)


def zone_to_dto(zone: Zone) -> ZoneDto:
    if zone.id is None or zone.location_id is None:
        raise ValueError("A persisted zone must have id and location_id")
    return ZoneDto(
        id=zone.id,
        location_id=zone.location_id,
        name=zone.name,
        moisture_threshold_low=zone.moisture_threshold_low,
        moisture_threshold_high=zone.moisture_threshold_high,
        schedule=zone.schedule,
    )


def location_config_to_dto(location: Location) -> LocationConfigDto:
    return LocationConfigDto(
        location=location_summary_to_dto(location),
        zones=[zone_to_dto(zone) for zone in location.zones],
    )
