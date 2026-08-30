"""Inward application port for deterministic approved-evidence retrieval (#51).

``EvidenceSearchPort`` is the Clean Architecure seam the future Gemini/ADK
layer uses to obtain reasoning/action-relevant authority. It accepts an
immutable :class:`EvidenceSearchQuery` and returns a typed
:class:`EvidenceSearchResult`. It exposes only approved, version-valid,
integrity-valid evidence — a source becomes authority only through this port
and the actual deterministic local retrieval path behind it.

The port is framework-free: no filesystem, no JSON, no Google/ADK/vector/HTTP
classes appear in the contract. The deterministic local adapter
(``ngabo.infrastructure.evidence``) supplies the implementation.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ngabo.application.value_objects.evidence_search import (
    EvidenceSearchQuery,
    EvidenceSearchResult,
)


@runtime_checkable
class EvidenceSearchPort(Protocol):
    """Inward contract for approved evidence retrieval by deterministic code."""

    def search(self, query: EvidenceSearchQuery) -> EvidenceSearchResult:
        """Retrieve approved evidence for ``query``.

        Args:
            query: The immutable approved-evidence retrieval request.

        Returns:
            A typed, versioned ``EvidenceSearchResult``. On ``SUCCESS`` the
            hits are exactly and only the approved sources/chunks that pass
            approval, version and integrity checks. A relevant-but-unsafe
            source returns ``NO_MATCH``/``SOURCE_NOT_FOUND``/
            ``UNAPPROVED_SOURCE``/``STALE_SOURCE``/``INTEGRITY_FAILURE`` — it
            is never returned with a warning.
        """
        ...

    def __call__(self, query: EvidenceSearchQuery) -> EvidenceSearchResult:
        """Callable protocol support for capability-style invocation."""
        ...
