from sqlalchemy.orm import Session

from src.application.automation.service import AutomationService
from src.application.overview.facade import LocationOverviewFacade
from src.infrastructure.persistence.automation_repository import SqlAlchemyAutomationRepository
from src.infrastructure.persistence.overview_repository import SqlAlchemyOverviewRepository


def build_overview_facade(session: Session) -> LocationOverviewFacade:
    strategy_repository = SqlAlchemyAutomationRepository(session)
    return LocationOverviewFacade(
        overview_repository=SqlAlchemyOverviewRepository(session),
        strategy_repository=strategy_repository,
        automation_service=AutomationService(strategy_repository),
    )
