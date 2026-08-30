"""Deterministic local approved-evidence adapter (Issue #51).

This package implements :class:`EvidenceSearchPort` against committed local
corpus material. Runtime retrieval is fully local: no network, no Google,
no vector/embedding search, no arbitrary web fetch. Approval, version and
integrity are all enforced deterministically before evidence may be returned
as reasoning/action-relevant authority.
"""

from ngabo.infrastructure.evidence.local_evidence_search import LocalEvidenceSearch

__all__ = ["LocalEvidenceSearch"]
