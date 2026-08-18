"""Framework-free value object for Ngabo incident identifiers.

Incident identifiers are opaque Ngabo-owned references with a stable,
documented shape: ``INC-`` followed by one or more digits, e.g. ``INC-001``
(see ``docs/AGENT_ARCHITECTURE.md``). The value object carries no
persistence or runtime behavior.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_INCIDENT_ID_PATTERN = re.compile(r"INC-\d+")


@dataclass(frozen=True)
class IncidentId:
    """Immutable identifier of a Ngabo incident."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not _INCIDENT_ID_PATTERN.fullmatch(self.value):
            raise ValueError(
                f"Invalid incident ID {self.value!r}; expected pattern 'INC-<digits>'"
            )

    def __str__(self) -> str:
        return self.value
