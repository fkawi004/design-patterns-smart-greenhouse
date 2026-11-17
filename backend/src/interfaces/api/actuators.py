from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.application.actuators.dto import ActuatorExecutionDto
from src.application.actuators.service import ActuatorExecutionService
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
