"""Deterministic source replay disposition enum (Issue #40)."""

from __future__ import annotations

from enum import StrEnum


class SourceReplayDisposition(StrEnum):
    """Deterministic comparison outcome between current and previous source states."""

    EXACT_REPLAY = "EXACT_REPLAY"
    MATERIAL_CHANGE = "MATERIAL_CHANGE"
