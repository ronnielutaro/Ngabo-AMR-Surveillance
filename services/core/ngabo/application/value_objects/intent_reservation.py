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
    lease_token: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.intent, HeroActionIntent):
            raise ValueError("intent must be a HeroActionIntent")
        if not isinstance(self.state, IntentState):
            raise ValueError("state must be an IntentState")
        if not isinstance(self.owned, bool):
            raise ValueError("owned must be a bool")
        if self.lease_token is not None and (
            not isinstance(self.lease_token, str) or not self.lease_token.strip()
        ):
            raise ValueError("lease_token must be non-blank text or None")
        if self.owned and not self.lease_token:
            raise ValueError("an owned reservation must carry a lease_token")
