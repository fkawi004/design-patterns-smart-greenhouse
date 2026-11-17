from sqlalchemy.orm import Session

from src.application.commands.service import CommandService
from src.domain.commands.invoker import CommandInvoker
from src.infrastructure.persistence.actuator_state_repository import (
    SqlAlchemyActuatorStateRepository,
)
from src.infrastructure.persistence.command_log_repository import (
    SqlAlchemyCommandLogRepository,
)
from src.interfaces.api.actuator_dependencies import build_actuator_port


def build_command_service(session: Session) -> CommandService:
    return CommandService(
        invoker=CommandInvoker(),
        actuator_port=build_actuator_port(session),
        state_repository=SqlAlchemyActuatorStateRepository(session),
        log_repository=SqlAlchemyCommandLogRepository(session),
    )
