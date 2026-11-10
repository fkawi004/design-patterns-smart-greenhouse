from sqlalchemy.orm import Session

from src.application.actuators.service import ActuatorExecutionService
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


def build_actuator_execution_service(session: Session) -> ActuatorExecutionService:
    state_repository = SqlAlchemyActuatorStateRepository(session)
    log_repository = SqlAlchemyExecutionLogRepository(session)
    adapter = SimulationActuatorAdapter()
    guarded_port = MaxRunTimeActuatorDecorator(adapter, state_repository)
    decorated_port = LoggingActuatorDecorator(guarded_port, log_repository)
    return ActuatorExecutionService(
        decorated_port=decorated_port,
        state_reader=state_repository,
        log_reader=log_repository,
    )
