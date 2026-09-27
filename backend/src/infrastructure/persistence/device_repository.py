from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.devices.entity import Device
from src.domain.sensors.entity import Sensor
from src.infrastructure.persistence.models import DeviceRow


class SqlAlchemySensorRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, sensor: Sensor) -> Sensor:
        row = DeviceRow(
            device_type=sensor.device_type,
            role="sensor",
            device_family="simulation",
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


class SqlAlchemyDeviceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, device: Device) -> Device:
        row = self._to_row(device)
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return self._to_device(row)

    def save_many(self, devices: list[Device]) -> list[Device]:
        rows = [self._to_row(device) for device in devices]
        self.session.add_all(rows)
        self.session.commit()
        for row in rows:
            self.session.refresh(row)
        return [self._to_device(row) for row in rows]

    def list_devices(
        self,
        device_family: str | None = None,
        role: str | None = None,
    ) -> list[Device]:
        statement = select(DeviceRow)
        if device_family is not None:
            statement = statement.where(DeviceRow.device_family == device_family)
        if role is not None:
            statement = statement.where(DeviceRow.role == role)
        statement = statement.order_by(DeviceRow.created_at.desc(), DeviceRow.display_name)
        rows = self.session.scalars(statement).all()
        return [self._to_device(row) for row in rows]

    @staticmethod
    def _to_row(device: Device) -> DeviceRow:
        return DeviceRow(
            device_type=device.device_type,
            role=device.role,
            device_family=device.device_family,
            display_name=device.display_name,
            default_config=device.default_config,
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
        )
