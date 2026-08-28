"""Framework-free value object for cryptographic source artifact digests (Issue #40).

Represents the raw artifact content digest ('What exact bytes did we receive?'),
distinct from the canonical logical SourceWatermark ('What AMR state was represented?').
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_HEX_64_PATTERN = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class SourceDigest:
    """Immutable content digest of a raw input source artifact."""

    algorithm: str
    hex_digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.algorithm, str) or self.algorithm != "sha256":
            raise ValueError(f"Invalid algorithm {self.algorithm!r}; expected 'sha256'")
        if not isinstance(self.hex_digest, str) or not _HEX_64_PATTERN.fullmatch(self.hex_digest):
            raise ValueError(
                f"Invalid hex_digest {self.hex_digest!r}; "
                "expected a 64-character lowercase hexadecimal string"
            )

    def __str__(self) -> str:
        return f"{self.algorithm}:{self.hex_digest}"
