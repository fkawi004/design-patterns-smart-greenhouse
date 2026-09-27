from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from src.application.devices.dto import DeviceDto
from src.application.locations.config_service import LocationConfigService
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
from src.application.locations.zone_assignment_service import ZoneAssignmentService
from src.domain.locations.errors import ConfigurationError
from src.infrastructure.db import get_session
from src.infrastructure.persistence.location_repository import (
    SqlAlchemyLocationRepository,
    SqlAlchemyZoneAssignmentRepository,
)

router = APIRouter(prefix="/api/locations", tags=["locations"])


def get_location_service(session: Session = Depends(get_session)) -> LocationConfigService:
    return LocationConfigService(SqlAlchemyLocationRepository(session))


def get_assignment_service(session: Session = Depends(get_session)) -> ZoneAssignmentService:
    return ZoneAssignmentService(SqlAlchemyZoneAssignmentRepository(session))


@router.post(
    "/config",
    response_model=LocationConfigDto,
    status_code=status.HTTP_201_CREATED,
)
def create_location_config(
    request: BuildLocationConfigRequestDto,
    service: LocationConfigService = Depends(get_location_service),
) -> LocationConfigDto:
    try:
        return service.build_and_save(request)
    except ConfigurationError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("", response_model=list[LocationSummaryDto])
def list_locations(
    service: LocationConfigService = Depends(get_location_service),
) -> list[LocationSummaryDto]:
    """List locations newest first."""
    return service.list_locations()


@router.get("/{location_id}/config", response_model=LocationConfigDto)
def get_location_config(
    location_id: UUID,
    service: LocationConfigService = Depends(get_location_service),
) -> LocationConfigDto:
    try:
        return service.get_config(location_id)
    except LocationNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(
    location_id: UUID,
    service: LocationConfigService = Depends(get_location_service),
) -> Response:
    try:
        service.delete_location(location_id)
    except LocationNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{location_id}/zones",
    response_model=ZoneDto,
    status_code=status.HTTP_201_CREATED,
)
def add_zone(
    location_id: UUID,
    request: ZoneWriteDto,
    service: LocationConfigService = Depends(get_location_service),
) -> ZoneDto:
    try:
        return service.add_zone(location_id, request)
    except ConfigurationError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except LocationNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.patch("/{location_id}/zones/{zone_id}", response_model=ZoneDto)
def update_zone(
    location_id: UUID,
    zone_id: UUID,
    request: ZoneWriteDto,
    service: LocationConfigService = Depends(get_location_service),
) -> ZoneDto:
    try:
        return service.update_zone(location_id, zone_id, request)
    except ConfigurationError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except (LocationNotFoundError, ZoneNotFoundError) as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.delete(
    "/{location_id}/zones/{zone_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_zone(
    location_id: UUID,
    zone_id: UUID,
    service: LocationConfigService = Depends(get_location_service),
) -> Response:
    try:
        service.delete_zone(location_id, zone_id)
    except LastZoneDeletionError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except (LocationNotFoundError, ZoneNotFoundError) as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{location_id}/zones/{zone_id}/devices",
    response_model=list[DeviceDto],
)
def list_zone_devices(
    location_id: UUID,
    zone_id: UUID,
    service: ZoneAssignmentService = Depends(get_assignment_service),
) -> list[DeviceDto]:
    try:
        return service.list_devices(location_id, zone_id)
    except ZoneNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
