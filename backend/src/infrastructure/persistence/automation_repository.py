from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.automation.context import LocationAutomationContext
from src.infrastructure.persistence.models import (
    AutomationRuleRow,
    DeviceRow,
    LocationRow,
    ReadingRow,
    ZoneRow,
)


class SqlAlchemyAutomationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def location_exists(self, location_id: UUID) -> bool:
        return self.session.get(LocationRow, location_id) is not None

    def get_strategy_key(self, location_id: UUID) -> str | None:
        return self.session.scalar(
            select(AutomationRuleRow.strategy_key).where(
                AutomationRuleRow.location_id == location_id
            )
        )

    def upsert_strategy(self, location_id: UUID, strategy_key: str) -> str:
        row = self.session.scalar(
            select(AutomationRuleRow).where(AutomationRuleRow.location_id == location_id)
        )
        if row is None:
            row = AutomationRuleRow(
                location_id=location_id,
                strategy_key=strategy_key,
                parameters={},
            )
            self.session.add(row)
        else:
            row.strategy_key = strategy_key
        self.session.commit()
        self.session.refresh(row)
        return row.strategy_key

    def load_contexts(self, location_id: UUID) -> list[LocationAutomationContext]:
        zones = self.session.scalars(
            select(ZoneRow)
            .where(ZoneRow.location_id == location_id)
            .order_by(ZoneRow.name, ZoneRow.id)
        ).all()
        return [
            LocationAutomationContext(
                location_id=location_id,
                zone_id=zone.id,
                zone_name=zone.name,
                latest_moisture=self._latest_moisture(zone.id),
                moisture_threshold_low=float(zone.moisture_threshold_low),
                moisture_threshold_high=float(zone.moisture_threshold_high),
            )
            for zone in zones
        ]

    def _latest_moisture(self, zone_id: UUID) -> float | None:
        value = self.session.scalar(
            select(ReadingRow.value)
            .join(DeviceRow, DeviceRow.id == ReadingRow.device_id)
            .where(
                DeviceRow.zone_id == zone_id,
                DeviceRow.role == "sensor",
                DeviceRow.device_type == "moisture_sensor",
            )
            .order_by(ReadingRow.recorded_at.desc(), ReadingRow.id.desc())
            .limit(1)
        )
        return float(value) if value is not None else None
