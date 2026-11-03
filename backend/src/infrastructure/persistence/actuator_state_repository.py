from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.infrastructure.persistence.models import ActuatorStateRow, DeviceRow


class SqlAlchemyActuatorStateRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_state(self, device_id: UUID) -> str | None:
        return self.session.scalar(
            select(ActuatorStateRow.state)
            .join(DeviceRow, DeviceRow.id == ActuatorStateRow.device_id)
            .where(
                ActuatorStateRow.device_id == device_id,
                DeviceRow.role == "actuator",
            )
        )

    def save_state(self, device_id: UUID, state: str) -> None:
        row = self.session.get(ActuatorStateRow, device_id)
        if row is None:
            raise LookupError("Actuator state disappeared during transition.")
        row.state = state
        self.session.commit()
