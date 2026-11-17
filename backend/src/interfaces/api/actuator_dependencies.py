from sqlalchemy.orm import Session

from src.application.actuators.service import ActuatorExecutionService
from src.domain.actuators.ports import ActuatorPort
from src.infrastructure.adapters.actuators.logging_decorator import (
    LoggingActuatorDecorator,
)
from src.infrastructure.adapters.actuators.max_runtime_decorator import (
    MaxRunTimeActuatorDecorator,
)
from src.infrastructure.adapters.actuators.simulation import SimulationActuatorAdapter
from src.infrastructure.persistence.actuator_state_repository import (
    SqlAlchemyActuatorStateRepository,
)
from src.infrastructure.persistence.execution_log_repository import (
    SqlAlchemyExecutionLogRepository,
)


def build_actuator_port(session: Session) -> ActuatorPort:
    state_repository = SqlAlchemyActuatorStateRepository(session)
    log_repository = SqlAlchemyExecutionLogRepository(session)
    adapter = SimulationActuatorAdapter()
    guarded_port = MaxRunTimeActuatorDecorator(adapter, state_repository)
    return LoggingActuatorDecorator(guarded_port, log_repository)


def build_actuator_execution_service(session: Session) -> ActuatorExecutionService:
    return ActuatorExecutionService(SqlAlchemyExecutionLogRepository(session))
