"""Typed parse result for the incident package boundary (#52).

``IncidentPackageParseFailure`` is one structured failure (stable code plus an
optional path/detail). ``IncidentPackageParseResult`` is the aggregate: either
``ok=True`` with a constructed immutable package, or ``ok=False`` with one or
more structured failures. It is framework-free and carries no verification or
authority semantics.
"""

from __future__ import annotations

from dataclasses import dataclass

from ngabo.application.enums.incident_package_error_code import IncidentPackageErrorCode
from ngabo.application.value_objects.incident_package import IncidentPackageCandidate


@dataclass(frozen=True)
class IncidentPackageParseFailure:
    """One structured failure produced by the package parse boundary."""

    code: IncidentPackageErrorCode
    path: tuple[str, ...] = ()
    detail: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.code, IncidentPackageErrorCode):
            raise ValueError(
                f"Invalid parse failure code {self.code!r}; "
                "expected an IncidentPackageErrorCode member"
            )
        if not isinstance(self.path, tuple):
            raise ValueError(f"Invalid parse failure path {self.path!r}; expected a tuple")
        for index, part in enumerate(self.path):
            if not isinstance(part, str) or not part:
                raise ValueError(
                    f"Invalid parse failure path element at position {index}: {part!r}"
                )
        if self.detail is not None and (
            not isinstance(self.detail, str) or not self.detail.strip()
        ):
            raise ValueError("detail must be non-blank text or None")


@dataclass(frozen=True)
class IncidentPackageParseResult:
    """Aggregate outcome of parsing a primitive into an incident package."""

    ok: bool
    package: IncidentPackageCandidate | None = None
    errors: tuple[IncidentPackageParseFailure, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.ok, bool):
            raise ValueError(f"Invalid parse ok {self.ok!r}; expected a bool")
        if self.package is not None and not isinstance(
            self.package, IncidentPackageCandidate
        ):
            raise ValueError("package must be an IncidentPackageCandidate or None")
        if not isinstance(self.errors, tuple):
            raise ValueError(f"Invalid parse errors {self.errors!r}; expected a tuple")
        for index, error in enumerate(self.errors):
            if not isinstance(error, IncidentPackageParseFailure):
                raise ValueError(
                    f"Invalid parse error at position {index}: {error!r}; "
                    "expected an IncidentPackageParseFailure"
                )
        if self.ok and self.package is None:
            raise ValueError("A successful parse result must carry a package")
        if self.ok and self.errors:
            raise ValueError("A successful parse result cannot carry errors")
        if not self.ok and self.package is not None:
            raise ValueError("A failed parse result cannot carry a package")
        if not self.ok and not self.errors:
            raise ValueError("A failed parse result must carry at least one error")
