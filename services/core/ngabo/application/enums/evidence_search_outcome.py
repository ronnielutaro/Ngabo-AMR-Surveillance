"""Stable outcomes for deterministic approved-evidence retrieval (Issue #51).

The retrieval path must distinguish "nothing relevant exists" from "relevant
source exists but cannot be trusted". These typed outcomes let downstream
orchestration decide whether to synthesize, abstain, or block without
overloading "no results" for an approval, integrity, or version failure.

Exactly the families #51 names: success, no-match, missing source, unapproved
source, stale source, integrity failure. Missing *chunk* is reported via the
same ``SOURCE_NOT_FOUND`` family because a manifest entry resolving to a
missing/invalid chunk is an unsafe source, not an ordinary empty result.
Unexpected programmer/infrastructure failures still raise; this vocabulary is
for the deterministic expected states.
"""

from __future__ import annotations

from enum import StrEnum


class EvidenceSearchOutcome(StrEnum):
    """Stable outcome of an approved-evidence search/lookup."""

    SUCCESS = "SUCCESS"
    NO_MATCH = "NO_MATCH"
    SOURCE_NOT_FOUND = "SOURCE_NOT_FOUND"
    UNAPPROVED_SOURCE = "UNAPPROVED_SOURCE"
    STALE_SOURCE = "STALE_SOURCE"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"
