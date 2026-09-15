from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.sensors.entity import Sensor
from src.infrastructure.persistence.models import DeviceRow


class SqlAlchemySensorRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, sensor: Sensor) -> Sensor:
        row = DeviceRow(
            device_type=sensor.device_type,
            role="sensor",
            display_name=sensor.display_name,
            default_config=sensor.default_config,
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return self._to_domain(row)

    def list_sensors(self) -> list[Sensor]:
        statement = (
            select(DeviceRow)
            .where(DeviceRow.role == "sensor")
            .order_by(DeviceRow.created_at.desc())
        )
        rows = self.session.scalars(statement).all()
        return [self._to_domain(row) for row in rows]

    @staticmethod
    def _to_domain(row: DeviceRow) -> Sensor:
        return Sensor(
            id=row.id,
            device_type=row.device_type,
            display_name=row.display_name or row.device_type,
            default_config=row.default_config,
        )
