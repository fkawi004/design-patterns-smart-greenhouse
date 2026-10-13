from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.domain.automation.context import LocationAutomationContext


class UnknownStrategyError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Recommendation:
    action: str
    reason: str
    score: float | None = None


class AutomationStrategy(ABC):
    key: str

    @abstractmethod
    def decide(self, context: LocationAutomationContext) -> Recommendation:
        raise NotImplementedError


class ConservativeMoistureStrategy(AutomationStrategy):
    key = "conservative"

    def decide(self, context: LocationAutomationContext) -> Recommendation:
        moisture = context.latest_moisture
        if moisture is None:
            return Recommendation("wait", "no moisture sensor reading in this zone")
        if moisture < context.moisture_threshold_low:
            return Recommendation(
                "irrigate",
                f"moisture {moisture:.2f} is below low threshold "
                f"{context.moisture_threshold_low:.2f}",
                score=context.moisture_threshold_low - moisture,
            )
        return Recommendation(
            "wait",
            f"moisture {moisture:.2f} is not below low threshold "
            f"{context.moisture_threshold_low:.2f}",
            score=0.0,
        )


class AggressiveMoistureStrategy(AutomationStrategy):
    key = "aggressive"

    def decide(self, context: LocationAutomationContext) -> Recommendation:
        moisture = context.latest_moisture
        if moisture is None:
            return Recommendation("wait", "no moisture sensor reading in this zone")
        if moisture < context.moisture_threshold_high:
            return Recommendation(
                "irrigate",
                f"moisture {moisture:.2f} is below high threshold "
                f"{context.moisture_threshold_high:.2f}",
                score=context.moisture_threshold_high - moisture,
            )
        return Recommendation(
            "wait",
            f"moisture {moisture:.2f} reached high threshold "
            f"{context.moisture_threshold_high:.2f}",
            score=0.0,
        )


STRATEGIES: dict[str, AutomationStrategy] = {
    strategy.key: strategy
    for strategy in (ConservativeMoistureStrategy(), AggressiveMoistureStrategy())
}


def get_strategy(key: str) -> AutomationStrategy:
    try:
        return STRATEGIES[key]
    except KeyError as error:
        raise UnknownStrategyError(f"Unknown automation strategy '{key}'.") from error
