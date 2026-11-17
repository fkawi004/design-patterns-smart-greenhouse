from typing import Any, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.commands.history import CommandLogEntry, CommandStatus
from src.infrastructure.persistence.models import CommandLogRow


class SqlAlchemyCommandLogRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def record(
        self,
        command_type: str,
        device_id: UUID,
        payload: dict[str, Any],
        status: CommandStatus,
        error_message: str | None,
    ) -> CommandLogEntry:
        row = CommandLogRow(
            command_type=command_type,
            device_id=device_id,
            payload=payload,
            status=status,
            error_message=error_message,
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return self._to_domain(row)

    def list_recent(self, limit: int) -> list[CommandLogEntry]:
        rows = self.session.scalars(
            select(CommandLogRow)
            .order_by(CommandLogRow.created_at.desc(), CommandLogRow.id.desc())
            .limit(limit)
        ).all()
        return [self._to_domain(row) for row in rows]

    @staticmethod
    def _to_domain(row: CommandLogRow) -> CommandLogEntry:
        return CommandLogEntry(
            id=row.id,
            command_type=row.command_type,
            device_id=row.device_id,
            payload=dict(row.payload),
            status=cast(CommandStatus, row.status),
            error_message=row.error_message,
            created_at=row.created_at,
        )
