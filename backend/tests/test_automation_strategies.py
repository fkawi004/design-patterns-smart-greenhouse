from uuid import uuid4

from src.domain.automation.context import LocationAutomationContext
from src.domain.automation.strategy import (
    AggressiveMoistureStrategy,
    ConservativeMoistureStrategy,
)


def context(moisture: float | None = 0.4) -> LocationAutomationContext:
    return LocationAutomationContext(
        location_id=uuid4(),
        zone_id=uuid4(),
        zone_name="Seedlings",
        latest_moisture=moisture,
        moisture_threshold_low=0.3,
        moisture_threshold_high=0.5,
    )


def test_conservative_waits_when_moisture_is_within_band() -> None:
    recommendation = ConservativeMoistureStrategy().decide(context())

    assert recommendation.action == "wait"
    assert "low threshold" in recommendation.reason


def test_aggressive_irrigates_for_same_context() -> None:
    recommendation = AggressiveMoistureStrategy().decide(context())

    assert recommendation.action == "irrigate"
    assert "high threshold" in recommendation.reason


def test_both_strategies_wait_without_a_zone_reading() -> None:
    missing = context(None)

    assert ConservativeMoistureStrategy().decide(missing).action == "wait"
    assert AggressiveMoistureStrategy().decide(missing).action == "wait"
    assert "no moisture sensor" in ConservativeMoistureStrategy().decide(missing).reason
