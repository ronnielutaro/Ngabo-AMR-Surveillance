"""Framework-free synthesis support manifest and evidence corpus metadata (#56).

``EvidenceCorpusMetadata`` is the immutable provenance of the approved-evidence
corpus a synthesis run is bound to. ``SynthesisSupportManifest`` captures the
ONLY record IDs, deterministic finding IDs, and approved evidence IDs the model
may cite. The model may reference nothing outside this manifest; deterministic
code rejects any unknown/fabricated reference, and any URL-as-support.

This is the structural boundary that keeps #56 model output provisioal and
grounded: support is bounded to what this run actually had available, and no
authority-bearing semantic can be smuggled in through references.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _require_nonblank(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"Invalid {label} {value!r}; expected non-blank text")
    return value


def _require_ids(values: object, label: str) -> frozenset[str]:
    if not isinstance(values, (frozenset, set, tuple, list)):
        raise ValueError(f"Invalid {label} {values!r}; expected an iterable of IDs")
    result: set[str] = set()
    for value in values:
        _require_nonblank(value, label)
        result.add(value)
    return frozenset(result)


@dataclass(frozen=True)
class EvidenceCorpusMetadata:
    """Immutable provenance metadata for the approved-evidence corpus."""

    corpus_id: str
    manifest_version: str
    corpus_digest: str

    def __post_init__(self) -> None:
        _require_nonblank(self.corpus_id, "evidence corpus id")
        _require_nonblank(self.manifest_version, "evidence manifest version")
        if (
            not isinstance(self.corpus_digest, str)
            or not _SHA256_PATTERN.fullmatch(self.corpus_digest)
        ):
            raise ValueError(
                f"Invalid evidence corpus digest {self.corpus_digest!r}; "
                "expected a 64-character lowercase hexadecimal digest"
            )


@dataclass(frozen=True)
class SynthesisSupportManifest:
    """The ONLY support identifiers a #56 model output may reference."""

    corpus_metadata: EvidenceCorpusMetadata
    record_ids: frozenset[str]
    finding_ids: frozenset[str]
    evidence_source_ids: frozenset[str]
    evidence_reference_ids: frozenset[str]

    def __post_init__(self) -> None:
        if not isinstance(self.corpus_metadata, EvidenceCorpusMetadata):
            raise ValueError("corpus_metadata must be an EvidenceCorpusMetadata")
        _require_ids(self.record_ids, "record_ids")
        _require_ids(self.finding_ids, "finding_ids")
        _require_ids(self.evidence_source_ids, "evidence_source_ids")
        _require_ids(self.evidence_reference_ids, "evidence_reference_ids")

    def to_safe_primitive(self) -> dict[str, object]:
        """Return a deterministic, secret-free primitive representation."""
        return {
            "corpus_id": self.corpus_metadata.corpus_id,
            "manifest_version": self.corpus_metadata.manifest_version,
            "corpus_digest": self.corpus_metadata.corpus_digest,
            "record_ids": sorted(self.record_ids),
            "finding_ids": sorted(self.finding_ids),
            "evidence_source_ids": sorted(self.evidence_source_ids),
            "evidence_reference_ids": sorted(self.evidence_reference_ids),
        }
