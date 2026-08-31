"""Result of durably creating/acquiring one logical ActionIntent (#176)."""

from __future__ import annotations

from dataclasses import dataclass

from ngabo.application.enums.intent_state import IntentState
from ngabo.application.value_objects.hero_action_intent import HeroActionIntent


@dataclass(frozen=True)
class IntentReservation:
    """Durable intent record plus dispatch-ownership result."""

    intent: HeroActionIntent
    state: IntentState
    owned: bool

    def __post_init__(self) -> None:
        if not isinstance(self.intent, HeroActionIntent):
            raise ValueError("intent must be a HeroActionIntent")
        if not isinstance(self.state, IntentState):
            raise ValueError("state must be an IntentState")
        if not isinstance(self.owned, bool):
            raise ValueError("owned must be a bool")
