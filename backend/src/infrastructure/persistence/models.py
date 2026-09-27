from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.persistence.base import Base


class DeviceRow(Base):
    __tablename__ = "devices"
    __table_args__ = (
        Index("ix_devices_family", "device_family"),
        Index("ix_devices_zone_id", "zone_id"),
        Index("ix_devices_location_id", "location_id"),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    device_type: Mapped[str] = mapped_column(String(64), nullable=False)
    role: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default=text("'sensor'"),
        index=True,
    )
    device_family: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default=text("'simulation'"),
    )
    display_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    default_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    zone_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("zones.id", ondelete="SET NULL", name="fk_devices_zone_id_zones"),
        nullable=True,
    )
    location_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "locations.id",
            ondelete="SET NULL",
            name="fk_devices_location_id_locations",
        ),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class LocationRow(Base):
    __tablename__ = "locations"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class ZoneRow(Base):
    __tablename__ = "zones"
    __table_args__ = (Index("ix_zones_location_id", "location_id"),)

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    location_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "locations.id",
            ondelete="CASCADE",
            name="fk_zones_location_id_locations",
        ),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    moisture_threshold_low: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    moisture_threshold_high: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    schedule: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
