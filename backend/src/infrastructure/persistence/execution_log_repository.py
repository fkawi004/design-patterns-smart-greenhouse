from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.actuators.execution import ActuatorExecution
from src.infrastructure.persistence.models import ActuatorExecutionLogRow


class SqlAlchemyExecutionLogRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def record(
        self,
        device_id: UUID,
        success: bool,
        policy_applied: list[str],
        message: str | None,
    ) -> ActuatorExecution:
        row = ActuatorExecutionLogRow(
            device_id=device_id,
            success=success,
            policy_applied=policy_applied,
            message=message,
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return self._to_domain(row)

    def list_recent(self, limit: int) -> list[ActuatorExecution]:
        rows = self.session.scalars(
            select(ActuatorExecutionLogRow)
            .order_by(
                ActuatorExecutionLogRow.created_at.desc(),
                ActuatorExecutionLogRow.id.desc(),
            )
            .limit(limit)
        ).all()
        return [self._to_domain(row) for row in rows]

    @staticmethod
    def _to_domain(row: ActuatorExecutionLogRow) -> ActuatorExecution:
        return ActuatorExecution(
            id=row.id,
            device_id=row.device_id,
            success=row.success,
            policy_applied=tuple(row.policy_applied),
            message=row.message,
            created_at=row.created_at,
        )
