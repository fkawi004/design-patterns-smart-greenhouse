from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.application.devices.dto import DeviceDto
from src.application.devices.family_service import DeviceFamilyService
from src.application.devices.mappers import device_to_dto
from src.application.locations.dto import ZoneAssignmentRequestDto
from src.application.locations.errors import DeviceNotFoundError, ZoneNotFoundError
from src.application.locations.zone_assignment_service import ZoneAssignmentService
from src.application.readings.dto import SamplingSettingsDto, SamplingSettingsRequestDto
from src.application.readings.errors import (
    ReadingDeviceNotFoundError,
    ReadingValidationError,
)
from src.application.readings.service import ReadingIngest
from src.domain.devices.family_factory import UnknownDeviceFamilyError
from src.infrastructure.db import get_session
from src.infrastructure.persistence.device_repository import SqlAlchemyDeviceRepository
from src.infrastructure.persistence.location_repository import SqlAlchemyZoneAssignmentRepository
from src.interfaces.api.reading_dependencies import build_reading_ingest

router = APIRouter(prefix="/api/devices", tags=["devices"])


def get_device_service(session: Session = Depends(get_session)) -> DeviceFamilyService:
    return DeviceFamilyService(SqlAlchemyDeviceRepository(session))


def get_assignment_service(session: Session = Depends(get_session)) -> ZoneAssignmentService:
    return ZoneAssignmentService(SqlAlchemyZoneAssignmentRepository(session))


def get_reading_ingest(session: Session = Depends(get_session)) -> ReadingIngest:
    return build_reading_ingest(session)


@router.get("", response_model=list[DeviceDto])
def list_devices(
    family: str | None = None,
    role: Literal["sensor", "actuator"] | None = None,
    service: DeviceFamilyService = Depends(get_device_service),
) -> list[DeviceDto]:
    return [device_to_dto(device) for device in service.list_devices(family, role)]


@router.post(
    "/provision",
    response_model=list[DeviceDto],
    status_code=status.HTTP_201_CREATED,
)
def provision_device_family(
    family: str = Query(min_length=1, examples=["simulation"]),
    service: DeviceFamilyService = Depends(get_device_service),
) -> list[DeviceDto]:
    try:
        devices = service.provision_family(family)
    except UnknownDeviceFamilyError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return [device_to_dto(device) for device in devices]


@router.patch("/{device_id}/zone", response_model=DeviceDto)
def assign_device_to_zone(
    device_id: UUID,
    request: ZoneAssignmentRequestDto,
    service: ZoneAssignmentService = Depends(get_assignment_service),
) -> DeviceDto:
    try:
        return service.assign(device_id, request.zone_id)
    except (DeviceNotFoundError, ZoneNotFoundError) as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.patch("/{device_id}/sampling", response_model=SamplingSettingsDto)
def update_device_sampling(
    device_id: UUID,
    request: SamplingSettingsRequestDto,
    ingest: ReadingIngest = Depends(get_reading_ingest),
) -> SamplingSettingsDto:
    try:
        return ingest.update_sampling(
            device_id,
            request.sampling_interval_seconds,
            request.tracking_enabled,
        )
    except ReadingDeviceNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ReadingValidationError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
