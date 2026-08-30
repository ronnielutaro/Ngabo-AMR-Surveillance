"""Framework-free evidence identity and chunk contracts (Issue #51).

``EvidenceSourceId`` and ``EvidenceReferenceId`` are the stable, opaque
Ngabo-owned identifiers for approved evidence sources and their retrievable
chunks. ``EvidenceChunk`` is the immutable retrieval unit: a stable reference
ID, a content bundle, its declared content digest and the deterministic tags
the local search matcher uses.

These value objects carry identity/structural validation only. Whether a
source is approved, version-valid, or intact is the responsibility of the
deterministic retrieval path (``EvidenceSearchPort`` and its local adapter),
not construction. A matching-chunk whose declared digest differs from its
content must be produced by the adapter as ``INTEGRITY_FAILURE`` before
authority, never silently returned.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_SOURCE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]*$")
_REFERENCE_ID_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9-]*::[A-Za-z0-9][A-Za-z0-9_-]*$"
)
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class EvidenceSourceId:
    """Stable opaque identifier of one approved evidence source.

    Shape is ``<PREFIX>-<IDENTIFIER>`` (e.g. ``WHO-AMR-001``). This is the
    same opaque ''source_id'' an ``ApprovedEvidenceReference`` (#28) points at.
    """

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not _SOURCE_ID_PATTERN.fullmatch(self.value):
            raise ValueError(
                f"Invalid evidence source ID {self.value!r}; "
                "expected the pattern '<PREFIX>-<IDENTIFIER>'"
            )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class EvidenceReferenceId:
    """Stable opaque identifier of one retrievable evidence chunk.

    Shape is ``<source_id>::<chunk-slug>`` (e.g.
    ``WHO-AMR-001::ipc-principle-01``). The prefix is the owning
    :class:`EvidenceSourceId`; the suffix is deterministic and stable.
    """

    value: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.value, str)
            or not _REFERENCE_ID_PATTERN.fullmatch(self.value)
        ):
            raise ValueError(
                f"Invalid evidence reference ID {self.value!r}; expected "
                "'<source_id>::<chunk-slug>'"
            )

    @property
    def source_id(self) -> str:
        """The owning source ID (the part before ``::``)."""
        return self.value.split("::", 1)[0]

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class EvidenceChunk:
    """Immutable retrievable chunk with content, digest and tags.

    The declared ``content_sha256`` is verified by the deterministic adapter
    *before* the chunk may be returned as authority. A mismatch is an
    ``INTEGRITY_FAILURE`` outcome, not a silently-degraded "result with a
    warning".
    """

    reference_id: EvidenceReferenceId
    source_id: EvidenceSourceId
    content: str
    content_sha256: str
    tags: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.reference_id, EvidenceReferenceId):
            raise ValueError("reference_id must be an EvidenceReferenceId")
        if not isinstance(self.source_id, EvidenceSourceId):
            raise ValueError("source_id must be an EvidenceSourceId")
        if self.reference_id.source_id != self.source_id.value:
            raise ValueError(
                f"reference_id {self.reference_id!r} must be owned by "
                f"source_id {self.source_id!r}"
            )
        if not isinstance(self.content, str):
            raise ValueError("content must be a str")
        if (
            not isinstance(self.content_sha256, str)
            or not _SHA256_PATTERN.fullmatch(self.content_sha256)
        ):
            raise ValueError(
                f"Invalid content_sha256 {self.content_sha256!r}; "
                "expected a 64-character lowercase hexadecimal digest"
            )
        if not isinstance(self.tags, tuple):
            raise ValueError(f"Invalid tags {self.tags!r}; expected a tuple")
        for index, tag in enumerate(self.tags):
            if not isinstance(tag, str) or not tag.strip():
                raise ValueError(
                    f"Invalid tag at position {index}: {tag!r}; expected non-blank text"
                )
