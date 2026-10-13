from typing import Protocol
from uuid import UUID

from src.application.automation.dto import RecommendationDto, StrategySelectionDto
from src.application.automation.errors import (
    AutomationContextError,
    AutomationLocationNotFoundError,
    AutomationRuleNotFoundError,
)
from src.domain.automation.context import LocationAutomationContext
from src.domain.automation.strategy import get_strategy


class AutomationRepository(Protocol):
    def location_exists(self, location_id: UUID) -> bool: ...

    def get_strategy_key(self, location_id: UUID) -> str | None: ...

    def upsert_strategy(self, location_id: UUID, strategy_key: str) -> str: ...

    def load_contexts(self, location_id: UUID) -> list[LocationAutomationContext]: ...


class AutomationService:
    def __init__(self, repository: AutomationRepository) -> None:
        self.repository = repository

    def get_strategy(self, location_id: UUID) -> StrategySelectionDto:
        self._ensure_location(location_id)
        key = self.repository.get_strategy_key(location_id)
        if key is None:
            raise AutomationRuleNotFoundError("Location has no saved automation strategy.")
        return StrategySelectionDto(location_id=location_id, strategy_key=key)

    def set_strategy(self, location_id: UUID, strategy_key: str) -> StrategySelectionDto:
        self._ensure_location(location_id)
        normalized_key = strategy_key.strip().lower()
        get_strategy(normalized_key)
        saved_key = self.repository.upsert_strategy(location_id, normalized_key)
        return StrategySelectionDto(location_id=location_id, strategy_key=saved_key)

    def evaluate(self, location_id: UUID) -> RecommendationDto:
        self._ensure_location(location_id)
        key = self.repository.get_strategy_key(location_id)
        if key is None:
            raise AutomationRuleNotFoundError("Location has no saved automation strategy.")
        strategy = get_strategy(key)
        contexts = self.repository.load_contexts(location_id)
        if not contexts:
            raise AutomationContextError("Location has no zones to evaluate.")

        decisions = [(context, strategy.decide(context)) for context in contexts]
        action = "irrigate" if any(item.action == "irrigate" for _, item in decisions) else "wait"
        reason = "; ".join(
            f"{context.zone_name}: {recommendation.action} because {recommendation.reason}"
            for context, recommendation in decisions
        )
        return RecommendationDto(
            location_id=location_id,
            strategy_key=key,
            action=action,
            reason=reason,
        )

    def _ensure_location(self, location_id: UUID) -> None:
        if not self.repository.location_exists(location_id):
            raise AutomationLocationNotFoundError("Location was not found.")
