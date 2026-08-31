"""Deterministic A1 action-policy verdict for the deadline hero (#176)."""

from __future__ import annotations

from dataclasses import dataclass

from ngabo.application.enums.hero_error_code import HeroErrorCode
from ngabo.domain.enums.action_class import ActionClass


@dataclass(frozen=True)
class HeroActionDecision:
    """Verdict of the deterministic A1 policy for one verified package."""

    auto_execute_a1: bool
    action_class: ActionClass
    authorized_target_id: str | None
    reason: str
    error_code: HeroErrorCode | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.auto_execute_a1, bool):
            raise ValueError("auto_execute_a1 must be a bool")
        if not isinstance(self.action_class, ActionClass):
            raise ValueError("action_class must be an ActionClass")
        if self.authorized_target_id is not None and (
            not isinstance(self.authorized_target_id, str)
            or not self.authorized_target_id.strip()
        ):
            raise ValueError("authorized_target_id must be non-blank text or None")
        if not isinstance(self.reason, str) or not self.reason:
            raise ValueError("reason must be non-blank text")
        if self.error_code is not None and not isinstance(
            self.error_code, HeroErrorCode
        ):
            raise ValueError("error_code must be a HeroErrorCode or None")
        if self.auto_execute_a1:
            if self.error_code is not None:
                raise ValueError("an auto-execute decision cannot carry an error_code")
            if self.authorized_target_id is None:
                raise ValueError("an auto-execute decision requires a target")
        else:
            if self.error_code is None:
                raise ValueError("a blocked decision must carry an error_code")
