from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.application.overview.dto import LocationOverviewDto
from src.application.overview.errors import OverviewLocationNotFoundError
from src.application.overview.facade import LocationOverviewFacade
from src.infrastructure.db import get_session
from src.interfaces.api.overview_dependencies import build_overview_facade

router = APIRouter(prefix="/api/locations", tags=["overview"])


def get_overview_facade(session: Session = Depends(get_session)) -> LocationOverviewFacade:
    return build_overview_facade(session)


@router.get("/{location_id}/overview", response_model=LocationOverviewDto)
def get_location_overview(
    location_id: UUID,
    facade: LocationOverviewFacade = Depends(get_overview_facade),
) -> LocationOverviewDto:
    try:
        return facade.get_overview(location_id)
    except OverviewLocationNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
