"""Shared deterministic authority/natural-language guard (#176).

One canonical guard, scoped to narrative text, rejects prohibited clinical/official
authority concepts in ordinary spaced and inflected forms. It is negation-aware
so safe language such as 'this does not confirm an outbreak' or 'the system does
not prescribe' is NOT blocked (the #56 false-positive bug is not recreated), while
an affirmative authority claim fails closed.
"""

from __future__ import annotations

import re

_AUTHORITY_RE = re.compile(
    # Inflected clinical/official authority stems (match the stem prefix).
    r"(?:\b(?:diagnos|prescri|treat|authoriz|approv|verif))"
    r"|(?:\b(?:"
    # Outbreak-confirmation, affirmative + passive + nominal forms.
    r"outbreak\s+(?:(?:has\s+been|was|were|is|are)\s+)?confirmed"
    r"|confirm(?:ed|ing)?\s+(?:(?:an?|the|any)\s+)?outbreak"
    r"|confirmation\s+of\s+(?:an?\s+)?outbreak"
    r"|outbreak\s+confirmation"
    r"|(?:official\s+)?outbreak\s+declaration"
    r"|declare[ds]?\s+(?:an?\s+)?outbreak"
    r"|outbreak_confirmed|mandatory_containment"
    r"|mandatory\s+containment|containment\s+order"
    r"|official\s+public\s+health\s+(?:declaration|declar)"
    r"|public\s+health\s+declaration"
    r"|notify\s+(?:the\s+)?(?:hospital|health\s+department|facility)"
    r"|action_ready|acknowledged"
    r"|send\s+samples\s+for\s+(?:treatment|testing)"
    r")\b)",
    re.I,
)

_COMPLETION_OR_AUTHORITY_RE = re.compile(
    r"\b(?:"
    r"escalate|auto_execute_a1|action_ready|acknowledged|package_completed|"
    r"investigation_complete|no_action_needed|delivered|sent|complete|done|"
    r"verified|approved|authorized|authorize|approve"
    r")\b",
    re.I,
)

_NEGATION_RE = re.compile(
    r"\b(?:not|no|never|cannot|can\s+not|has\s+not|have\s+not|was\s+not|were\s+not|"
    r"is\s+not|are\s+not|does\s+not|did\s+not|do\s+not|without|unable\s+to|"
    r"has\s+not\s+been|was\s+not\s+been|not\s+been)\b",
    re.I,
)


def _negated_before(text: str, start: int) -> bool:
    """Return True if the clause immediately before ``start`` is negated."""
    # Scan backward to the start of the current clause (after a sentence/clause
    # separator) and look for a negation token in the trailing window.
    clause_start = max(
        text.rfind(";", 0, start),
        text.rfind(".", 0, start),
        text.rfind("!", 0, start),
        text.rfind("?", 0, start),
        text.rfind(",", 0, start),
        text.rfind("\n", 0, start),
    )
    window = text[clause_start + 1 : start]
    return bool(_NEGATION_RE.search(window[-40:]))


def contains_forbidden_authority(text: str) -> bool:
    """Return True if ``text`` asserts a forbidden clinical/official authority."""
    if not isinstance(text, str) or not text:
        return False
    for match in _AUTHORITY_RE.finditer(text):
        if _negated_before(text, match.start()):
            continue
        return True
    return False


def asserts_forbidden_authority_or_completion(text: str) -> bool:
    """Stricter check used by the package verifier.

    Retains the explicit completion/authority denials (ESCALATE, AUTO_EXECUTE_A1,
    PACKAGE_COMPLETED, INVESTIGATION_COMPLETE, DELIVERED, NO_ACTION_NEEDED,
    VERIFIED, APPROVED, AUTHORIZED, COMPLETE) in addition to the natural-language
    clinical/official authority matcher.
    """
    if not isinstance(text, str) or not text:
        return False
    return contains_forbidden_authority(text) or bool(
        _COMPLETION_OR_AUTHORITY_RE.search(text)
    )
