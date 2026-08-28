"""Deterministic import outcome disposition enum (Issue #44)."""

from __future__ import annotations

from enum import StrEnum


class ImportOutcomeDisposition(StrEnum):
    """Application-level outcome disposition of a canonical source import."""

    FIRST_IMPORT = "FIRST_IMPORT"
    EXACT_REPLAY = "EXACT_REPLAY"
    MATERIAL_CHANGE = "MATERIAL_CHANGE"
    FAILED = "FAILED"
