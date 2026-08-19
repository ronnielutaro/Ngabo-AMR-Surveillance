"""Unit tests for the autonomy action contract (Issue #27 / M1B.3).

The expected classification matrix and canonical reason strings are written
out explicitly here so the autonomy semantics are reviewable without
reverse-engineering the implementation.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from ngabo.domain.enums.action_class import ActionClass
from ngabo.domain.enums.autonomy_decision_status import AutonomyDecisionStatus
from ngabo.domain.exceptions import InvalidAutonomyDecisionError
from ngabo.domain.value_objects.autonomy_decision import (
    AUTONOMY_CLASSIFICATION_CONTRACT,
    REASON_A0,
    REASON_A1,
    REASON_A2,
    REASON_A3,
    AutonomyDecision,
)

EXPECTED_CLASSES = (
    ActionClass.INTERNAL_STATE,
    ActionClass.SAFE_EXTERNAL_COORDINATION,
    ActionClass.REAL_OPERATIONAL_ESCALATION,
    ActionClass.CLINICAL_OR_OFFICIAL_PUBLIC_HEALTH_DECISION,
)

EXPECTED_STATUSES = (
    AutonomyDecisionStatus.AUTONOMOUS_ELIGIBLE,
    AutonomyDecisionStatus.GATES_REQUIRED,
    AutonomyDecisionStatus.BLOCKED,
)

EXPECTED_REASON_A0 = (
    "A0 INTERNAL_STATE: autonomous internal incident/package/audit state work "
    "is eligible at this classification level; carries no external-action "
    "semantics and authorizes no external effect."
)
EXPECTED_REASON_A1 = (
    "A1 SAFE_EXTERNAL_COORDINATION: belongs to the potentially autonomous "
    "safe-coordination lane; classification alone authorizes nothing — later "
    "deterministic gates (verified package, allow-listed target, "
    "authorization, freshness, ActionIntent/idempotency) remain required."
)
EXPECTED_REASON_A2 = (
    "A2 REAL_OPERATIONAL_ESCALATION: outside the default autonomous "
    "public-v0.1 envelope; autonomous execution is blocked — any escalation "
    "requires separate explicit authorization outside the autonomous flow."
)
EXPECTED_REASON_A3 = (
    "A3 CLINICAL_OR_OFFICIAL_PUBLIC_HEALTH_DECISION: prescribing, treatment, "
    "diagnosis, official outbreak confirmation/declaration, or equivalent "
    "consequential authority; never autonomously executable in v0.1."
)

EXPECTED_CONTRACT: dict[ActionClass, tuple[AutonomyDecisionStatus, str]] = {
    ActionClass.INTERNAL_STATE: (
        AutonomyDecisionStatus.AUTONOMOUS_ELIGIBLE,
        EXPECTED_REASON_A0,
    ),
    ActionClass.SAFE_EXTERNAL_COORDINATION: (
        AutonomyDecisionStatus.GATES_REQUIRED,
        EXPECTED_REASON_A1,
    ),
    ActionClass.REAL_OPERATIONAL_ESCALATION: (
        AutonomyDecisionStatus.BLOCKED,
        EXPECTED_REASON_A2,
    ),
    ActionClass.CLINICAL_OR_OFFICIAL_PUBLIC_HEALTH_DECISION: (
        AutonomyDecisionStatus.BLOCKED,
        EXPECTED_REASON_A3,
    ),
}


def _forbidden_combinations() -> list[tuple[ActionClass, AutonomyDecisionStatus]]:
    valid_status = {cls: status for cls, (status, _reason) in EXPECTED_CONTRACT.items()}
    return [
        (cls, status)
        for cls in EXPECTED_CLASSES
        for status in EXPECTED_STATUSES
        if valid_status[cls] is not status
    ]


class TestDeclaredActionClasses:
    @pytest.mark.parametrize(
        ("action_class", "expected_value"),
        [
            (ActionClass.INTERNAL_STATE, "A0"),
            (ActionClass.SAFE_EXTERNAL_COORDINATION, "A1"),
            (ActionClass.REAL_OPERATIONAL_ESCALATION, "A2"),
            (ActionClass.CLINICAL_OR_OFFICIAL_PUBLIC_HEALTH_DECISION, "A3"),
        ],
    )
    def test_stable_value(self, action_class: ActionClass, expected_value: str) -> None:
        assert action_class.value == expected_value
        assert str(action_class) == expected_value

    def test_exactly_four_canonical_classes(self) -> None:
        assert tuple(ActionClass) == EXPECTED_CLASSES


class TestDeclaredDecisionStatuses:
    @pytest.mark.parametrize(
        ("status", "expected_value"),
        [
            (AutonomyDecisionStatus.AUTONOMOUS_ELIGIBLE, "AUTONOMOUS_ELIGIBLE"),
            (AutonomyDecisionStatus.GATES_REQUIRED, "GATES_REQUIRED"),
            (AutonomyDecisionStatus.BLOCKED, "BLOCKED"),
        ],
    )
    def test_stable_value(self, status: AutonomyDecisionStatus, expected_value: str) -> None:
        assert status.value == expected_value
        assert str(status) == expected_value

    def test_exactly_three_statuses(self) -> None:
        assert tuple(AutonomyDecisionStatus) == EXPECTED_STATUSES


class TestClassificationContract:
    def test_contract_matches_expected_matrix(self) -> None:
        assert AUTONOMY_CLASSIFICATION_CONTRACT == EXPECTED_CONTRACT

    @pytest.mark.parametrize(
        ("reason", "expected_reason"),
        [
            (REASON_A0, EXPECTED_REASON_A0),
            (REASON_A1, EXPECTED_REASON_A1),
            (REASON_A2, EXPECTED_REASON_A2),
            (REASON_A3, EXPECTED_REASON_A3),
        ],
    )
    def test_canonical_reason_is_exact(self, reason: str, expected_reason: str) -> None:
        assert reason == expected_reason

    def test_reasons_are_distinct(self) -> None:
        assert len({REASON_A0, REASON_A1, REASON_A2, REASON_A3}) == 4


class TestContractRuntimeImmutability:
    """Regression coverage for the Issue #27 review fix.

    The classification contract is exposed as a runtime-immutable mapping;
    mutation attempts must raise so the A2/A3 blocks cannot be rewritten
    behind the validator's back.
    """

    def _attempt_upgrade(
        self, action_class: ActionClass, status: AutonomyDecisionStatus
    ) -> None:
        with pytest.raises(TypeError):
            AUTONOMY_CLASSIFICATION_CONTRACT[action_class] = (  # type: ignore[index]
                status,
                "attempted runtime upgrade",
            )

    def test_item_assignment_is_rejected_for_every_class(self) -> None:
        for action_class in EXPECTED_CLASSES:
            self._attempt_upgrade(
                action_class, AutonomyDecisionStatus.AUTONOMOUS_ELIGIBLE
            )

    def test_item_deletion_is_rejected(self) -> None:
        with pytest.raises(TypeError):
            del AUTONOMY_CLASSIFICATION_CONTRACT[  # type: ignore[attr-defined]
                ActionClass.REAL_OPERATIONAL_ESCALATION
            ]

    def test_a2_cannot_become_autonomously_eligible(self) -> None:
        self._attempt_upgrade(
            ActionClass.REAL_OPERATIONAL_ESCALATION,
            AutonomyDecisionStatus.AUTONOMOUS_ELIGIBLE,
        )
        assert (
            AUTONOMY_CLASSIFICATION_CONTRACT[ActionClass.REAL_OPERATIONAL_ESCALATION]
            == EXPECTED_CONTRACT[ActionClass.REAL_OPERATIONAL_ESCALATION]
        )
        decision = AutonomyDecision.for_class(ActionClass.REAL_OPERATIONAL_ESCALATION)
        assert decision.status is AutonomyDecisionStatus.BLOCKED

    def test_a3_cannot_become_autonomously_eligible(self) -> None:
        self._attempt_upgrade(
            ActionClass.CLINICAL_OR_OFFICIAL_PUBLIC_HEALTH_DECISION,
            AutonomyDecisionStatus.AUTONOMOUS_ELIGIBLE,
        )
        assert (
            AUTONOMY_CLASSIFICATION_CONTRACT[
                ActionClass.CLINICAL_OR_OFFICIAL_PUBLIC_HEALTH_DECISION
            ]
            == EXPECTED_CONTRACT[ActionClass.CLINICAL_OR_OFFICIAL_PUBLIC_HEALTH_DECISION]
        )
        decision = AutonomyDecision.for_class(
            ActionClass.CLINICAL_OR_OFFICIAL_PUBLIC_HEALTH_DECISION
        )
        assert decision.status is AutonomyDecisionStatus.BLOCKED

    def test_a1_remains_gates_required(self) -> None:
        self._attempt_upgrade(
            ActionClass.SAFE_EXTERNAL_COORDINATION,
            AutonomyDecisionStatus.AUTONOMOUS_ELIGIBLE,
        )
        assert (
            AUTONOMY_CLASSIFICATION_CONTRACT[ActionClass.SAFE_EXTERNAL_COORDINATION]
            == EXPECTED_CONTRACT[ActionClass.SAFE_EXTERNAL_COORDINATION]
        )
        decision = AutonomyDecision.for_class(ActionClass.SAFE_EXTERNAL_COORDINATION)
        assert decision.status is AutonomyDecisionStatus.GATES_REQUIRED

    def test_for_class_behavior_unchanged_after_mutation_attempts(self) -> None:
        self._attempt_upgrade(
            ActionClass.INTERNAL_STATE, AutonomyDecisionStatus.BLOCKED
        )
        for action_class in EXPECTED_CLASSES:
            status, reason = EXPECTED_CONTRACT[action_class]
            decision = AutonomyDecision.for_class(action_class)
            assert decision.action_class is action_class
            assert decision.status is status
            assert decision.reason == reason


class TestValidDecisions:
    @pytest.mark.parametrize("action_class", EXPECTED_CLASSES)
    def test_for_class_builds_canonical_decision(self, action_class: ActionClass) -> None:
        decision = AutonomyDecision.for_class(action_class)
        expected_status, expected_reason = EXPECTED_CONTRACT[action_class]
        assert decision.action_class is action_class
        assert decision.status is expected_status
        assert decision.reason == expected_reason

    @pytest.mark.parametrize("action_class", EXPECTED_CLASSES)
    def test_explicit_canonical_construction_equivalent(
        self, action_class: ActionClass
    ) -> None:
        status, reason = EXPECTED_CONTRACT[action_class]
        explicit = AutonomyDecision(action_class, status, reason)
        assert explicit == AutonomyDecision.for_class(action_class)
        assert hash(explicit) == hash(AutonomyDecision.for_class(action_class))

    def test_value_semantics(self) -> None:
        first = AutonomyDecision.for_class(ActionClass.INTERNAL_STATE)
        second = AutonomyDecision.for_class(ActionClass.INTERNAL_STATE)
        assert first == second
        assert first is not second
        assert first != object()


class TestImpossibleCombinations:
    @pytest.mark.parametrize(("action_class", "status"), _forbidden_combinations())
    def test_forbidden_status_fails_closed(
        self, action_class: ActionClass, status: AutonomyDecisionStatus
    ) -> None:
        _expected_status, reason = EXPECTED_CONTRACT[action_class]
        with pytest.raises(InvalidAutonomyDecisionError) as excinfo:
            AutonomyDecision(action_class, status, reason)
        error = excinfo.value
        assert error.action_class is action_class
        assert error.status is status
        assert str(action_class) in str(error)

    @pytest.mark.parametrize("action_class", EXPECTED_CLASSES)
    def test_non_canonical_reason_fails_closed(self, action_class: ActionClass) -> None:
        status, _reason = EXPECTED_CONTRACT[action_class]
        with pytest.raises(InvalidAutonomyDecisionError):
            AutonomyDecision(
                action_class, status, "a rewritten reason the contract does not permit"
            )


class TestCriticalSafetyInvariants:
    @pytest.mark.parametrize(
        "action_class",
        [
            ActionClass.REAL_OPERATIONAL_ESCALATION,
            ActionClass.CLINICAL_OR_OFFICIAL_PUBLIC_HEALTH_DECISION,
        ],
    )
    def test_a2_and_a3_cannot_be_autonomously_executable(
        self, action_class: ActionClass
    ) -> None:
        decision = AutonomyDecision.for_class(action_class)
        assert decision.status is AutonomyDecisionStatus.BLOCKED
        for status in (
            AutonomyDecisionStatus.AUTONOMOUS_ELIGIBLE,
            AutonomyDecisionStatus.GATES_REQUIRED,
        ):
            with pytest.raises(InvalidAutonomyDecisionError):
                AutonomyDecision(action_class, status, EXPECTED_CONTRACT[action_class][1])

    def test_a1_is_not_automatically_authorized(self) -> None:
        decision = AutonomyDecision.for_class(ActionClass.SAFE_EXTERNAL_COORDINATION)
        assert decision.status is AutonomyDecisionStatus.GATES_REQUIRED
        with pytest.raises(InvalidAutonomyDecisionError):
            AutonomyDecision(
                ActionClass.SAFE_EXTERNAL_COORDINATION,
                AutonomyDecisionStatus.AUTONOMOUS_ELIGIBLE,
                EXPECTED_REASON_A1,
            )

    def test_a0_grants_no_external_execution_authority(self) -> None:
        decision = AutonomyDecision.for_class(ActionClass.INTERNAL_STATE)
        assert decision.status is AutonomyDecisionStatus.AUTONOMOUS_ELIGIBLE
        assert "no external" in decision.reason


class TestUnknownInputFailsClosed:
    def test_raw_string_action_class_is_rejected(self) -> None:
        with pytest.raises(InvalidAutonomyDecisionError):
            AutonomyDecision(
                "A1",  # type: ignore[arg-type]
                AutonomyDecisionStatus.GATES_REQUIRED,
                EXPECTED_REASON_A1,
            )

    def test_none_action_class_is_rejected(self) -> None:
        with pytest.raises(InvalidAutonomyDecisionError):
            AutonomyDecision(None, AutonomyDecisionStatus.BLOCKED, EXPECTED_REASON_A2)  # type: ignore[arg-type]

    def test_raw_string_status_is_rejected(self) -> None:
        with pytest.raises(InvalidAutonomyDecisionError):
            AutonomyDecision(
                ActionClass.INTERNAL_STATE,
                "AUTONOMOUS_ELIGIBLE",  # type: ignore[arg-type]
                EXPECTED_REASON_A0,
            )

    def test_for_class_rejects_unknown_input(self) -> None:
        with pytest.raises(InvalidAutonomyDecisionError):
            AutonomyDecision.for_class("A1")  # type: ignore[arg-type]
        with pytest.raises(InvalidAutonomyDecisionError):
            AutonomyDecision.for_class(None)  # type: ignore[arg-type]


class TestImmutability:
    def test_decisions_are_frozen(self) -> None:
        decision = AutonomyDecision.for_class(ActionClass.INTERNAL_STATE)
        with pytest.raises(FrozenInstanceError):
            decision.status = AutonomyDecisionStatus.BLOCKED  # type: ignore[misc]

    def test_decisions_are_hashable(self) -> None:
        decision = AutonomyDecision.for_class(ActionClass.INTERNAL_STATE)
        assert {decision: "x"}[AutonomyDecision.for_class(ActionClass.INTERNAL_STATE)] == "x"


class TestDeterministicBehavior:
    def test_repeated_for_class_is_stable(self) -> None:
        for action_class in EXPECTED_CLASSES:
            first = AutonomyDecision.for_class(action_class)
            for _ in range(3):
                assert AutonomyDecision.for_class(action_class) == first
