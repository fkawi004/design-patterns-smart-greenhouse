from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.application.devices.dto import DeviceDto
from src.application.devices.family_service import DeviceFamilyService
from src.application.devices.mappers import device_to_dto
from src.domain.devices.family_factory import UnknownDeviceFamilyError
from src.infrastructure.db import get_session
from src.infrastructure.persistence.device_repository import SqlAlchemyDeviceRepository

router = APIRouter(prefix="/api/devices", tags=["devices"])


def get_device_service(session: Session = Depends(get_session)) -> DeviceFamilyService:
    return DeviceFamilyService(SqlAlchemyDeviceRepository(session))


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
