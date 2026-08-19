"""Unit tests for the deterministic incident lifecycle (Issue #26 / M1B.2).

The expected allowed-transition matrix is written out explicitly here so the
lifecycle graph is reviewable without reverse-engineering the implementation.
"""

from __future__ import annotations

import pytest

from ngabo.domain.enums.incident_state import IncidentState
from ngabo.domain.exceptions import InvalidIncidentTransitionError
from ngabo.domain.services.incident_transitions import (
    ALLOWED_INCIDENT_TRANSITIONS,
    TERMINAL_INCIDENT_STATES,
    can_transition,
    validate_transition,
)

ALL_STATES = tuple(IncidentState)

EXPECTED_ALLOWED: dict[IncidentState, frozenset[IncidentState]] = {
    IncidentState.INVESTIGATING: frozenset(
        {
            IncidentState.COMPLETED,
            IncidentState.NEEDS_INFORMATION,
            IncidentState.INSUFFICIENT_APPROVED_EVIDENCE,
            IncidentState.VALIDATION_FAILED,
            IncidentState.POLICY_BLOCKED,
            IncidentState.STALE_RECOMPUTE_REQUIRED,
            IncidentState.ACTION_FAILED_RETRYABLE,
            IncidentState.ACTION_FAILED_TERMINAL,
        }
    ),
    IncidentState.STALE_RECOMPUTE_REQUIRED: frozenset({IncidentState.INVESTIGATING}),
    IncidentState.ACTION_FAILED_RETRYABLE: frozenset(
        {IncidentState.COMPLETED, IncidentState.ACTION_FAILED_TERMINAL}
    ),
}

EXPECTED_TERMINAL = (
    IncidentState.COMPLETED,
    IncidentState.NEEDS_INFORMATION,
    IncidentState.INSUFFICIENT_APPROVED_EVIDENCE,
    IncidentState.VALIDATION_FAILED,
    IncidentState.POLICY_BLOCKED,
    IncidentState.ACTION_FAILED_TERMINAL,
)


def _allowed_edges() -> list[tuple[IncidentState, IncidentState]]:
    return [
        (current, requested)
        for current, requested_set in EXPECTED_ALLOWED.items()
        for requested in requested_set
    ]


def _forbidden_edges() -> list[tuple[IncidentState, IncidentState]]:
    allowed = set(_allowed_edges())
    return [
        (current, requested)
        for current in ALL_STATES
        for requested in ALL_STATES
        if (current, requested) not in allowed and current is not requested
    ]


class TestDeclaredStates:
    @pytest.mark.parametrize(
        ("state", "expected_value"),
        [
            (IncidentState.INVESTIGATING, "INVESTIGATING"),
            (IncidentState.COMPLETED, "COMPLETED"),
            (IncidentState.NEEDS_INFORMATION, "NEEDS_INFORMATION"),
            (IncidentState.INSUFFICIENT_APPROVED_EVIDENCE, "INSUFFICIENT_APPROVED_EVIDENCE"),
            (IncidentState.VALIDATION_FAILED, "VALIDATION_FAILED"),
            (IncidentState.POLICY_BLOCKED, "POLICY_BLOCKED"),
            (IncidentState.STALE_RECOMPUTE_REQUIRED, "STALE_RECOMPUTE_REQUIRED"),
            (IncidentState.ACTION_FAILED_RETRYABLE, "ACTION_FAILED_RETRYABLE"),
            (IncidentState.ACTION_FAILED_TERMINAL, "ACTION_FAILED_TERMINAL"),
        ],
    )
    def test_stable_value(self, state: IncidentState, expected_value: str) -> None:
        assert state.value == expected_value
        assert str(state) == expected_value


class TestTransitionGraphContract:
    def test_implementation_matches_expected_allowed_matrix(self) -> None:
        assert ALLOWED_INCIDENT_TRANSITIONS == EXPECTED_ALLOWED

    def test_terminal_states_match_expected(self) -> None:
        assert frozenset(EXPECTED_TERMINAL) == TERMINAL_INCIDENT_STATES

    def test_every_state_is_key_or_terminal(self) -> None:
        covered = set(ALLOWED_INCIDENT_TRANSITIONS) | set(TERMINAL_INCIDENT_STATES)
        assert covered == set(ALL_STATES)

    def test_terminal_states_have_no_outgoing_edges(self) -> None:
        for terminal in TERMINAL_INCIDENT_STATES:
            assert terminal not in ALLOWED_INCIDENT_TRANSITIONS

    def test_non_terminal_states_have_an_outgoing_edge(self) -> None:
        for state in ALL_STATES:
            if state not in TERMINAL_INCIDENT_STATES:
                assert state in ALLOWED_INCIDENT_TRANSITIONS
                assert len(ALLOWED_INCIDENT_TRANSITIONS[state]) >= 1


class TestAllowedTransitions:
    @pytest.mark.parametrize(("current", "requested"), _allowed_edges())
    def test_allowed_transition_passes(
        self, current: IncidentState, requested: IncidentState
    ) -> None:
        assert can_transition(current, requested) is True
        validate_transition(current, requested)


class TestForbiddenTransitions:
    @pytest.mark.parametrize(("current", "requested"), _forbidden_edges())
    def test_forbidden_transition_fails_closed(
        self, current: IncidentState, requested: IncidentState
    ) -> None:
        assert can_transition(current, requested) is False
        with pytest.raises(InvalidIncidentTransitionError) as excinfo:
            validate_transition(current, requested)
        error = excinfo.value
        assert error.current is current
        assert error.requested is requested
        assert str(current) in str(error)
        assert str(requested) in str(error)


class TestSameStateTransitions:
    @pytest.mark.parametrize("state", ALL_STATES)
    def test_same_state_request_is_rejected(self, state: IncidentState) -> None:
        assert can_transition(state, state) is False
        with pytest.raises(InvalidIncidentTransitionError):
            validate_transition(state, state)


class TestTerminalStatesCannotReopen:
    @pytest.mark.parametrize("terminal", EXPECTED_TERMINAL)
    def test_terminal_state_has_no_exits(self, terminal: IncidentState) -> None:
        for requested in ALL_STATES:
            assert can_transition(terminal, requested) is False
            with pytest.raises(InvalidIncidentTransitionError):
                validate_transition(terminal, requested)


class TestFailClosedOnUnknownInput:
    def test_raw_string_input_is_rejected(self) -> None:
        assert can_transition("INVESTIGATING", IncidentState.COMPLETED) is False  # type: ignore[arg-type]
        assert can_transition(IncidentState.INVESTIGATING, "COMPLETED") is False  # type: ignore[arg-type]
        assert can_transition(None, None) is False  # type: ignore[arg-type]

    def test_validate_raises_domain_error_for_unknown_input(self) -> None:
        with pytest.raises(InvalidIncidentTransitionError):
            validate_transition("INVESTIGATING", IncidentState.COMPLETED)  # type: ignore[arg-type]


class TestDeterministicBehavior:
    def test_repeated_evaluation_is_stable(self) -> None:
        for current, requested in _allowed_edges() + _forbidden_edges():
            first = can_transition(current, requested)
            for _ in range(3):
                assert can_transition(current, requested) is first
