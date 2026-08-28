"""Status taxonomy for resistance profile similarity comparisons (Issue #45)."""

from __future__ import annotations

from enum import StrEnum


class ProfileSimilarityStatus(StrEnum):
    """Outcome status for a pairwise resistance profile similarity evaluation.

    Differentiates valid numeric similarity calculations from deterministic
    abstentions (insufficient panel overlap, biological incompatibility, or
    self-comparison).
    """

    SUCCESS = "SUCCESS"
    """Comparable antibiotic panel meets minimum threshold; numeric similarity computed."""

    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    """Fewer than minimum required comparable antibiotics shared between profiles."""

    INCOMPATIBLE_ORGANISM = "INCOMPATIBLE_ORGANISM"
    """Organisms are biologically incompatible for profile similarity comparison."""

    IDENTICAL_INPUTS = "IDENTICAL_INPUTS"
    """Same isolate record compared with itself; rejected from manufacturing cluster evidence."""
