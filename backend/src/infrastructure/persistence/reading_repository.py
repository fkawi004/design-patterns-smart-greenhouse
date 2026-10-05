from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.devices.entity import Device
from src.domain.sensors.reading import Reading
from src.infrastructure.persistence.models import DeviceRow, ReadingRow


class SqlAlchemyReadingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_device(self, device_id: UUID) -> Device | None:
        row = self.session.get(DeviceRow, device_id)
        return self._to_device(row) if row else None

    def insert(self, reading: Reading) -> Reading:
        row = ReadingRow(
            device_id=reading.device_id,
            value=reading.value,
            unit=reading.unit,
            source=reading.source,
            recorded_at=reading.recorded_at,
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return self._to_reading(row)

    def list_for_device(self, device_id: UUID, limit: int = 20) -> list[Reading]:
        rows = self.session.scalars(
            select(ReadingRow)
            .where(ReadingRow.device_id == device_id)
            .order_by(ReadingRow.recorded_at.desc(), ReadingRow.id.desc())
            .limit(limit)
        ).all()
        return [self._to_reading(row) for row in rows]

    def latest_for_device(self, device_id: UUID) -> Reading | None:
        readings = self.list_for_device(device_id, limit=1)
        return readings[0] if readings else None

    def list_tracking_sensors(self) -> list[Device]:
        rows = self.session.scalars(
            select(DeviceRow)
            .where(
                DeviceRow.role == "sensor",
                DeviceRow.tracking_enabled.is_(True),
            )
            .order_by(DeviceRow.id)
        ).all()
        return [self._to_device(row) for row in rows]

    def update_sampling(
        self,
        device_id: UUID,
        sampling_interval_seconds: int,
        tracking_enabled: bool,
    ) -> Device | None:
        row = self.session.get(DeviceRow, device_id)
        if row is None:
            return None
        row.sampling_interval_seconds = sampling_interval_seconds
        row.tracking_enabled = tracking_enabled
        self.session.commit()
        self.session.refresh(row)
        return self._to_device(row)

    @staticmethod
    def _to_reading(row: ReadingRow) -> Reading:
        return Reading(
            device_id=row.device_id,
            value=float(row.value),
            unit=row.unit,
            source=row.source,
            recorded_at=row.recorded_at,
        )

    @staticmethod
    def _to_device(row: DeviceRow) -> Device:
        return Device(
            id=row.id,
            device_type=row.device_type,
            role=row.role,
            device_family=row.device_family,
            display_name=row.display_name or row.device_type,
            default_config=row.default_config,
            zone_id=row.zone_id,
            location_id=row.location_id,
            sampling_interval_seconds=row.sampling_interval_seconds,
            tracking_enabled=row.tracking_enabled,
        )
