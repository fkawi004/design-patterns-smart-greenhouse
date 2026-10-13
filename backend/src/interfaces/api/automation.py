from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.application.automation.dto import (
    RecommendationDto,
    StrategyKeyRequestDto,
    StrategySelectionDto,
)
from src.application.automation.errors import (
    AutomationContextError,
    AutomationLocationNotFoundError,
    AutomationRuleNotFoundError,
)
from src.application.automation.service import AutomationService
from src.domain.automation.strategy import UnknownStrategyError
from src.infrastructure.db import get_session
from src.infrastructure.persistence.automation_repository import SqlAlchemyAutomationRepository

router = APIRouter(prefix="/api/locations", tags=["automation"])


def get_automation_service(session: Session = Depends(get_session)) -> AutomationService:
    return AutomationService(SqlAlchemyAutomationRepository(session))


@router.get("/{location_id}/automation", response_model=StrategySelectionDto)
def get_location_strategy(
    location_id: UUID,
    service: AutomationService = Depends(get_automation_service),
) -> StrategySelectionDto:
    try:
        return service.get_strategy(location_id)
    except AutomationLocationNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except AutomationRuleNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.put("/{location_id}/automation", response_model=StrategySelectionDto)
def set_location_strategy(
    location_id: UUID,
    request: StrategyKeyRequestDto,
    service: AutomationService = Depends(get_automation_service),
) -> StrategySelectionDto:
    try:
        return service.set_strategy(location_id, request.strategy_key)
    except AutomationLocationNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except UnknownStrategyError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/{location_id}/automation/evaluate", response_model=RecommendationDto)
def evaluate_location(
    location_id: UUID,
    service: AutomationService = Depends(get_automation_service),
) -> RecommendationDto:
    try:
        return service.evaluate(location_id)
    except AutomationLocationNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except AutomationRuleNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except AutomationContextError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except UnknownStrategyError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
