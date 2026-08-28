"""Deterministic WHONET CSV parse result value object (M2.2 / Issue #39)."""

from __future__ import annotations

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

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError(f"Invalid success {self.success!r}; expected bool")
        if not isinstance(self.records, tuple):
            raise TypeError(f"Invalid records {self.records!r}; expected a tuple")
        for index, record in enumerate(self.records):
            if not isinstance(record, CanonicalIsolate):
                raise TypeError(
                    f"Invalid record at position {index}: {record!r}; expected CanonicalIsolate"
                )
        if not isinstance(self.errors, tuple):
            raise TypeError(f"Invalid errors {self.errors!r}; expected a tuple")
        for index, err in enumerate(self.errors):
            if not isinstance(err, WhonetParserError):
                raise TypeError(
                    f"Invalid error at position {index}: {err!r}; expected WhonetParserError"
                )

        if self.success:
            if self.errors:
                raise ValueError("A successful parse result must not contain errors.")
            if not self.records:
                raise ValueError("A successful parse result must contain at least one record.")
            if not isinstance(self.batch, CanonicalImportBatch):
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
