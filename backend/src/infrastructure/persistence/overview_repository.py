from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.domain.devices.entity import Device
from src.domain.locations.entity import Location, Zone
from src.domain.sensors.reading import Reading
from src.infrastructure.persistence.models import DeviceRow, LocationRow, ReadingRow, ZoneRow


class SqlAlchemyOverviewRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_location_with_zones(self, location_id: UUID) -> Location | None:
        rows = self.session.execute(
            select(LocationRow, ZoneRow)
            .outerjoin(ZoneRow, ZoneRow.location_id == LocationRow.id)
            .where(LocationRow.id == location_id)
            .order_by(ZoneRow.name, ZoneRow.id)
        ).all()
        if not rows:
            return None
        location_row = rows[0][0]
        zones = tuple(self._to_zone(zone_row) for _, zone_row in rows if zone_row is not None)
        return Location(id=location_row.id, name=location_row.name, zones=zones)

    def list_assigned_devices(self, location_id: UUID) -> list[Device]:
        rows = self.session.scalars(
            select(DeviceRow)
            .where(
                DeviceRow.location_id == location_id,
                DeviceRow.zone_id.is_not(None),
            )
            .order_by(DeviceRow.zone_id, DeviceRow.display_name, DeviceRow.id)
        ).all()
        return [self._to_device(row) for row in rows]

    def latest_readings(self, device_ids: list[UUID]) -> dict[UUID, Reading]:
        if not device_ids:
            return {}
        ranked_readings = (
            select(
                ReadingRow.device_id,
                ReadingRow.value,
                ReadingRow.unit,
                ReadingRow.source,
                ReadingRow.recorded_at,
                func.row_number()
                .over(
                    partition_by=ReadingRow.device_id,
                    order_by=(ReadingRow.recorded_at.desc(), ReadingRow.id.desc()),
                )
                .label("reading_rank"),
            )
            .where(ReadingRow.device_id.in_(device_ids))
            .subquery()
        )
        rows = self.session.execute(
            select(ranked_readings).where(ranked_readings.c.reading_rank == 1)
        ).mappings()
        return {
            row["device_id"]: Reading(
                device_id=row["device_id"],
                value=float(row["value"]),
                unit=row["unit"],
                source=row["source"],
                recorded_at=row["recorded_at"],
            )
            for row in rows
        }

    @staticmethod
    def _to_zone(row: ZoneRow) -> Zone:
        return Zone(
            id=row.id,
            location_id=row.location_id,
            name=row.name,
            moisture_threshold_low=float(row.moisture_threshold_low),
            moisture_threshold_high=float(row.moisture_threshold_high),
            schedule=row.schedule,
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
