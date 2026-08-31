"""Shared deterministic authority/natural-language guard (#176).

Rejects prohibited clinical/official authority concepts in ordinary spaced and
inflected forms (not only internal enum-like tokens), scoped to the narrative
text being checked so the #56 false-positive bug is not recreated. Used by both
the outgoing A1 coordination-payload validator and the hero package verifier.
"""

from __future__ import annotations

import re

_AUTHORITY_RE = re.compile(
    r"(?:\b(?:diagnos|prescrib|treat|authoriz|approv|verif))"
    r"|(?:\b(?:"
    r"outbreak\s+(?:is\s+)?confirmed"
    r"|confirm(?:ed)?\s+(?:(?:an?|the)\s+)?outbreak"
    r"|declare[ds]?\s+(?:an?\s+)?outbreak"
    r"|outbreak\s+declaration|outbreak_confirmed"
    r"|mandatory\s+containment|containment\s+order|mandatory_containment"
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


def contains_forbidden_authority(text: str) -> bool:
    """Return True if ``text`` asserts a forbidden clinical/official authority."""
    if not isinstance(text, str) or not text:
        return False
    return bool(_AUTHORITY_RE.search(text))


def asserts_forbidden_authority_or_completion(text: str) -> bool:
    """Stricter check used by the package verifier.

    Retains the explicit completion/authority denials (ESCALATE, AUTO_EXECUTE_A1,
    PACKAGE_COMPLETED, INVESTIGATION_COMPLETE, DELIVERED, NO_ACTION_NEEDED,
    VERIFIED, APPROVED, AUTHORIZED, COMPLETE) in addition to the natural-language
    clinical/official authority matcher. The narrower ``contains_forbidden_authority``
    remains for the outgoing coordination payload to avoid the benign-word
    false positives already encountered in #56.
    """
    if not isinstance(text, str) or not text:
        return False
    return bool(_AUTHORITY_RE.search(text) or _COMPLETION_OR_AUTHORITY_RE.search(text))
