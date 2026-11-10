from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.actuators.state import ActuatorStateSnapshot
from src.infrastructure.persistence.models import ActuatorStateRow, DeviceRow


class SqlAlchemyActuatorStateRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_state(self, device_id: UUID) -> str | None:
        snapshot = self.get_snapshot(device_id)
        return snapshot.state if snapshot is not None else None

    def get_snapshot(self, device_id: UUID) -> ActuatorStateSnapshot | None:
        row = self.session.execute(
            select(ActuatorStateRow.state, ActuatorStateRow.updated_at)
            .join(DeviceRow, DeviceRow.id == ActuatorStateRow.device_id)
            .where(
                ActuatorStateRow.device_id == device_id,
                DeviceRow.role == "actuator",
            )
        ).one_or_none()
        if row is None:
            return None
        return ActuatorStateSnapshot(state=row.state, updated_at=row.updated_at)

    def save_state(self, device_id: UUID, state: str) -> None:
        row = self.session.get(ActuatorStateRow, device_id)
        if row is None:
            raise LookupError("Actuator state disappeared during transition.")
        row.state = state
        self.session.commit()
