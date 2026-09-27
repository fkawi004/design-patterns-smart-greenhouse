from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from src.domain.devices.entity import Device
from src.domain.locations.entity import Location, LocationConfig, Zone
from src.infrastructure.persistence.models import DeviceRow, LocationRow, ZoneRow


class SqlAlchemyLocationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save_config(self, config: LocationConfig) -> Location:
        try:
            location_row = LocationRow(name=config.location.name)
            self.session.add(location_row)
            self.session.flush()
            zone_rows = [
                ZoneRow(
                    location_id=location_row.id,
                    name=zone.name,
                    moisture_threshold_low=zone.moisture_threshold_low,
                    moisture_threshold_high=zone.moisture_threshold_high,
                    schedule=zone.schedule,
                )
                for zone in config.location.zones
            ]
            self.session.add_all(zone_rows)
            self.session.commit()
            for row in zone_rows:
                self.session.refresh(row)
            return self._to_location(location_row, zone_rows)
        except Exception:
            self.session.rollback()
            raise

    def get_config(self, location_id: UUID) -> Location | None:
        location_row = self.session.get(LocationRow, location_id)
        if location_row is None:
            return None
        zone_rows = self.session.scalars(
            select(ZoneRow)
            .where(ZoneRow.location_id == location_id)
            .order_by(ZoneRow.name, ZoneRow.id)
        ).all()
        return self._to_location(location_row, zone_rows)

    def list_locations(self) -> list[Location]:
        rows = self.session.scalars(
            select(LocationRow).order_by(LocationRow.created_at.desc(), LocationRow.id.desc())
        ).all()
        return [Location(id=row.id, name=row.name, zones=()) for row in rows]

    def delete_location(self, location_id: UUID) -> bool:
        row = self.session.get(LocationRow, location_id)
        if row is None:
            return False
        try:
            self.session.execute(
                update(DeviceRow)
                .where(DeviceRow.location_id == location_id)
                .values(zone_id=None, location_id=None)
            )
            self.session.delete(row)
            self.session.commit()
            return True
        except Exception:
            self.session.rollback()
            raise

    def add_zone(self, location_id: UUID, zone: Zone) -> Zone | None:
        if self.session.get(LocationRow, location_id) is None:
            return None
        row = ZoneRow(
            location_id=location_id,
            name=zone.name,
            moisture_threshold_low=zone.moisture_threshold_low,
            moisture_threshold_high=zone.moisture_threshold_high,
            schedule=zone.schedule,
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return self._to_zone(row)

    def update_zone(self, location_id: UUID, zone_id: UUID, zone: Zone) -> Zone | None:
        row = self.session.scalar(
            select(ZoneRow).where(
                ZoneRow.id == zone_id,
                ZoneRow.location_id == location_id,
            )
        )
        if row is None:
            return None
        row.name = zone.name
        row.moisture_threshold_low = zone.moisture_threshold_low
        row.moisture_threshold_high = zone.moisture_threshold_high
        row.schedule = zone.schedule
        self.session.commit()
        self.session.refresh(row)
        return self._to_zone(row)

    def delete_zone(self, location_id: UUID, zone_id: UUID) -> bool:
        row = self.session.scalar(
            select(ZoneRow).where(
                ZoneRow.id == zone_id,
                ZoneRow.location_id == location_id,
            )
        )
        if row is None:
            return False
        try:
            self.session.execute(
                update(DeviceRow)
                .where(DeviceRow.zone_id == zone_id)
                .values(zone_id=None, location_id=None)
            )
            self.session.delete(row)
            self.session.commit()
            return True
        except Exception:
            self.session.rollback()
            raise

    @classmethod
    def _to_location(cls, row: LocationRow, zone_rows: list[ZoneRow]) -> Location:
        return Location(
            id=row.id,
            name=row.name,
            zones=tuple(cls._to_zone(zone) for zone in zone_rows),
        )

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


class SqlAlchemyZoneAssignmentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_device(self, device_id: UUID) -> Device | None:
        row = self.session.get(DeviceRow, device_id)
        return self._to_device(row) if row else None

    def get_zone(self, zone_id: UUID) -> Zone | None:
        row = self.session.get(ZoneRow, zone_id)
        return SqlAlchemyLocationRepository._to_zone(row) if row else None

    def save_assignment(self, device_id: UUID, zone: Zone | None) -> Device:
        row = self.session.get(DeviceRow, device_id)
        if row is None:
            raise LookupError("Device disappeared during assignment.")
        row.zone_id = zone.id if zone else None
        row.location_id = zone.location_id if zone else None
        self.session.commit()
        self.session.refresh(row)
        return self._to_device(row)

    def list_zone_devices(self, location_id: UUID, zone_id: UUID) -> list[Device] | None:
        zone = self.session.scalar(
            select(ZoneRow).where(
                ZoneRow.id == zone_id,
                ZoneRow.location_id == location_id,
            )
        )
        if zone is None:
            return None
        rows = self.session.scalars(
            select(DeviceRow)
            .where(DeviceRow.zone_id == zone_id)
            .order_by(DeviceRow.display_name, DeviceRow.id)
        ).all()
        return [self._to_device(row) for row in rows]

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
        )
