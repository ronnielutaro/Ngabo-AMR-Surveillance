"""Deterministic resistance profile representation (Issue #45)."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING

from ngabo.domain.enums.interpretation import Interpretation

if TYPE_CHECKING:
    from ngabo.domain.entities.canonical_isolate import CanonicalIsolate

ISOLATE_ID_PATTERN = re.compile(r"^ISO-\d{3}$")
ANTIBIOTIC_CODE_PATTERN = re.compile(r"^[A-Z]{2,6}$")


@dataclass(frozen=True)
class ResistanceProfile:
    """Immutable, framework-free resistance profile derived from canonical AST observations.

    Captures only the scientific identity, organism grouping, and AST observations
    required for phenotype comparison. Does not include unrelated patient or location
    metadata.
    """

    isolate_id: str
    organism_code: str
    organism_name: str
    observations: Mapping[str, Interpretation]
    tested_antibiotics: tuple[str, ...]
    known_antibiotics: tuple[str, ...]
    unknown_antibiotics: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.isolate_id, str) or not ISOLATE_ID_PATTERN.fullmatch(
            self.isolate_id
        ):
            raise ValueError(
                f"Invalid isolate ID {self.isolate_id!r}; expected {ISOLATE_ID_PATTERN.pattern}"
            )
        if not isinstance(self.organism_code, str) or not self.organism_code.strip():
            raise ValueError("organism_code must be a non-empty string")
        if not isinstance(self.organism_name, str) or not self.organism_name.strip():
            raise ValueError("organism_name must be a non-empty string")
        if not isinstance(self.observations, Mapping) or not self.observations:
            raise ValueError(
                "observations must be a non-empty mapping of antimicrobial observations"
            )

        checked_obs: dict[str, Interpretation] = {}
        for code, interp in self.observations.items():
            if not isinstance(code, str) or not ANTIBIOTIC_CODE_PATTERN.fullmatch(code):
                raise ValueError(
                    f"Invalid antimicrobial code {code!r}; "
                    f"expected {ANTIBIOTIC_CODE_PATTERN.pattern}"
                )
            if not isinstance(interp, Interpretation):
                raise TypeError(
                    f"Invalid interpretation for {code!r}: {interp!r}; expected Interpretation enum"
                )
            checked_obs[code] = interp

        sorted_tested = tuple(sorted(checked_obs.keys()))
        sorted_known = tuple(
            code
            for code in sorted_tested
            if checked_obs[code]
            in (
                Interpretation.SUSCEPTIBLE,
                Interpretation.INTERMEDIATE,
                Interpretation.RESISTANT,
            )
        )
        sorted_unknown = tuple(
            code
            for code in sorted_tested
            if checked_obs[code] == Interpretation.UNKNOWN
        )

        object.__setattr__(self, "observations", MappingProxyType(checked_obs))
        object.__setattr__(self, "tested_antibiotics", sorted_tested)
        object.__setattr__(self, "known_antibiotics", sorted_known)
        object.__setattr__(self, "unknown_antibiotics", sorted_unknown)

    @classmethod
    def from_canonical_isolate(cls, isolate: CanonicalIsolate) -> ResistanceProfile:
        """Derive an immutable ResistanceProfile from a CanonicalIsolate."""
        obs = {
            code: ast_entry.interpretation
            for code, ast_entry in isolate.ast_results.items()
        }
        return cls(
            isolate_id=isolate.isolate_id,
            organism_code=isolate.organism_code,
            organism_name=isolate.organism_name,
            observations=obs,
            tested_antibiotics=(),  # computed in __post_init__
            known_antibiotics=(),   # computed in __post_init__
            unknown_antibiotics=(), # computed in __post_init__
        )
