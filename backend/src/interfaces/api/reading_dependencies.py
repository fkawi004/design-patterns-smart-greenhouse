from sqlalchemy.orm import Session

from src.application.readings.service import ReadingIngest
from src.infrastructure.adapters.sensors.selector import SensorAdapterSelector
from src.infrastructure.persistence.reading_repository import SqlAlchemyReadingRepository


def build_reading_ingest(session: Session) -> ReadingIngest:
    return ReadingIngest(
        SqlAlchemyReadingRepository(session),
        SensorAdapterSelector(),
    )
