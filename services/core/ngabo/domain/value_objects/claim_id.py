"""Framework-free value object for Ngabo reasoning-claim identifiers.

Claim identifiers are opaque Ngabo-owned references with a stable,
documented shape: ``claim-`` followed by one or more digits, e.g.
``claim-01`` (canonical claim schema in
``docs/PROOF_CARRYING_REASONING.md`` §5, M1B.4 / Issue #28). The value
object carries no persistence or resolution behavior; whether a referenced
claim actually exists is checked by the later deterministic verifier (#29).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_CLAIM_ID_PATTERN = re.compile(r"claim-\d+")


@dataclass(frozen=True)
class ClaimId:
    """Immutable identifier of a Ngabo reasoning claim."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not _CLAIM_ID_PATTERN.fullmatch(self.value):
            raise ValueError(
                f"Invalid claim ID {self.value!r}; expected pattern 'claim-<digits>'"
            )

    def __str__(self) -> str:
        return self.value
