"""Deterministic WHONET CSV parse result value object (M2.2 / Issue #39)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ngabo.domain.entities.canonical_import_batch import CanonicalImportBatch
from ngabo.domain.entities.canonical_isolate import CanonicalIsolate
from ngabo.interfaces.parsers.whonet_parser_error import WhonetParserError


@dataclass(frozen=True)
class WhonetParseResult:
    """Immutable result of parsing and normalizing a WHONET-style CSV."""

    success: bool
    records: tuple[CanonicalIsolate, ...]
    batch: CanonicalImportBatch | None
    errors: tuple[WhonetParserError, ...]
    raw_candidates: tuple[Mapping[str, object], ...] = ()

    def __post_init__(self) -> None:
        if self.success:
            if self.errors:
                raise ValueError("A successful parse result must not contain errors.")
            if not self.records:
                raise ValueError("A successful parse result must contain at least one record.")
            if self.batch is None:
                raise ValueError("A successful parse result must provide a CanonicalImportBatch.")
            if self.batch.records != self.records:
                raise ValueError("The batch records must match the parse result records.")
        else:
            if not self.errors:
                raise ValueError("An unsuccessful parse result must contain at least one error.")
            if self.records:
                raise ValueError("An unsuccessful parse result must not expose parsed records.")
            if self.batch is not None:
                raise ValueError("An unsuccessful parse result must not expose an import batch.")
