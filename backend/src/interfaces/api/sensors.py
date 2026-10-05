from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.application.readings.dto import ReadingDto
from src.application.readings.errors import (
    ReadingDeviceNotFoundError,
    ReadingValidationError,
)
from src.application.readings.service import ReadingIngest
from src.application.sensors.service import SensorService
from src.domain.sensors.creators import UnknownSensorTypeError
from src.domain.sensors.entity import Sensor
from src.infrastructure.adapters.sensors.errors import SensorAdapterError
from src.infrastructure.db import get_session
from src.infrastructure.persistence.device_repository import SqlAlchemySensorRepository
from src.interfaces.api.reading_dependencies import build_reading_ingest

router = APIRouter(prefix="/api/sensors", tags=["sensors"])


class SensorCreateRequest(BaseModel):
    type: str = Field(min_length=1, examples=["moisture"])
    display_name: str | None = Field(default=None, max_length=128)


class SensorResponse(BaseModel):
    id: UUID
    device_type: str
    display_name: str
    default_config: dict[str, Any]
    sampling_interval_seconds: int
    tracking_enabled: bool


def get_sensor_service(session: Session = Depends(get_session)) -> SensorService:
    return SensorService(SqlAlchemySensorRepository(session))


def get_reading_ingest(session: Session = Depends(get_session)) -> ReadingIngest:
    return build_reading_ingest(session)


def to_response(sensor: Sensor) -> SensorResponse:
    if sensor.id is None:
        raise RuntimeError("A persisted sensor must have an id")
    return SensorResponse(
        id=sensor.id,
        device_type=sensor.device_type,
        display_name=sensor.display_name,
        default_config=sensor.default_config,
        sampling_interval_seconds=sensor.sampling_interval_seconds,
        tracking_enabled=sensor.tracking_enabled,
    )


@router.get("", response_model=list[SensorResponse])
def list_sensors(service: SensorService = Depends(get_sensor_service)) -> list[SensorResponse]:
    return [to_response(sensor) for sensor in service.list_sensors()]


@router.post("", response_model=SensorResponse, status_code=status.HTTP_201_CREATED)
def create_sensor(
    request: SensorCreateRequest,
    service: SensorService = Depends(get_sensor_service),
) -> SensorResponse:
    try:
        sensor = service.create_sensor(request.type, request.display_name)
    except UnknownSensorTypeError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return to_response(sensor)


@router.post(
    "/{sensor_id}/read",
    response_model=ReadingDto,
    status_code=status.HTTP_201_CREATED,
)
def read_sensor(
    sensor_id: UUID,
    ingest: ReadingIngest = Depends(get_reading_ingest),
) -> ReadingDto:
    try:
        return ingest.take_reading(sensor_id)
    except ReadingDeviceNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except (ReadingValidationError, SensorAdapterError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/{sensor_id}/readings", response_model=list[ReadingDto])
def list_sensor_readings(
    sensor_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    ingest: ReadingIngest = Depends(get_reading_ingest),
) -> list[ReadingDto]:
    try:
        return ingest.list_readings(sensor_id, limit)
    except ReadingDeviceNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ReadingValidationError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
