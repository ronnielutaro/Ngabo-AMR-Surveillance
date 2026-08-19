"""Framework-free value object for Ngabo canonical source-state watermarks.

A source watermark is an opaque token identifying the canonical source state
that produced an investigation. Watermarks are compared by value equality to
prove currency before autonomous action (ADR 0006, ADR 0008). Freshness
checking and source hashing are intentionally out of scope for this value
object.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceWatermark:
    """Immutable opaque token of the canonical source state at investigation time."""

    value: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.value, str)
            or not self.value.strip()
            or self.value != self.value.strip()
        ):
            raise ValueError(
                "Invalid source watermark; expected a non-empty string without "
                "leading/trailing whitespace"
            )

    def __str__(self) -> str:
        return self.value
