from uuid import UUID, uuid4

from src.application.automation.service import AutomationService
from src.domain.automation.context import LocationAutomationContext


class FakeAutomationRepository:
    def __init__(self, location_id: UUID) -> None:
        self.location_id = location_id
        self.strategy_key = "conservative"
        self.contexts = [
            LocationAutomationContext(
                location_id=location_id,
                zone_id=uuid4(),
                zone_name="Measured zone",
                latest_moisture=0.4,
                moisture_threshold_low=0.3,
                moisture_threshold_high=0.5,
            ),
            LocationAutomationContext(
                location_id=location_id,
                zone_id=uuid4(),
                zone_name="Empty zone",
                latest_moisture=None,
                moisture_threshold_low=0.2,
                moisture_threshold_high=0.45,
            ),
        ]

    def location_exists(self, location_id: UUID) -> bool:
        return location_id == self.location_id

    def get_strategy_key(self, location_id: UUID) -> str | None:
        return self.strategy_key if self.location_exists(location_id) else None

    def upsert_strategy(self, location_id: UUID, strategy_key: str) -> str:
        self.strategy_key = strategy_key
        return strategy_key

    def load_contexts(self, location_id: UUID) -> list[LocationAutomationContext]:
        return self.contexts if self.location_exists(location_id) else []


def test_service_uses_saved_key_and_documents_every_zone() -> None:
    location_id = uuid4()
    repository = FakeAutomationRepository(location_id)
    service = AutomationService(repository)

    conservative = service.evaluate(location_id)
    service.set_strategy(location_id, "aggressive")
    aggressive = service.evaluate(location_id)

    assert conservative.strategy_key == "conservative"
    assert conservative.action == "wait"
    assert aggressive.strategy_key == "aggressive"
    assert aggressive.action == "irrigate"
    assert "Measured zone" in aggressive.reason
    assert "Empty zone: wait because no moisture sensor reading" in aggressive.reason
