from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from src.application.actuators.dto import (
    ActuatorApplyRequestDto,
    ActuatorExecutionDto,
)
from src.application.actuators.service import ActuatorExecutionService
from src.application.devices.errors import ActuatorNotFoundError
from src.domain.actuators.ports import ActuatorPolicyError
from src.infrastructure.db import get_session
from src.interfaces.api.actuator_dependencies import build_actuator_execution_service

router = APIRouter(prefix="/api/actuators", tags=["actuators"])


def get_actuator_execution_service(
    session: Session = Depends(get_session),
) -> ActuatorExecutionService:
    return build_actuator_execution_service(session)


@router.get("/executions", response_model=list[ActuatorExecutionDto])
def list_actuator_executions(
    limit: int = Query(default=20, ge=1, le=100),
    service: ActuatorExecutionService = Depends(get_actuator_execution_service),
) -> list[ActuatorExecutionDto]:
    return service.list_executions(limit)


@router.post("/{device_id}/apply", status_code=status.HTTP_204_NO_CONTENT)
def apply_actuator_command(
    device_id: UUID,
    request: ActuatorApplyRequestDto,
    service: ActuatorExecutionService = Depends(get_actuator_execution_service),
) -> Response:
    try:
        service.apply(device_id, request.command, request.payload)
    except ActuatorNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ActuatorPolicyError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
