"""Application ports — inward-facing framework-free contracts.

Ports here are Protocols that application workflows depend on and outer
layers (interfaces/infrastructure) implement; see
``docs/CLEAN_ARCHITECTURE.md``. May depend on ``ngabo.domain`` only. Must
never import framework/vendor SDKs or outer Ngabo layers.

Populated issue by issue:
- Issue #29: ``VerifyReasoningClaims`` (M1B.5)
- Issue #44: ``LoadImportSource``, ``SourceReplayRepository``, ``ParseCanonicalSource`` (M2.4)
"""

from __future__ import annotations

from ngabo.application.ports.load_import_source import LoadImportSource
from ngabo.application.ports.parse_canonical_source import (
    ParseCanonicalSource,
    ParsedSourceError,
    ParsedSourceResult,
)
from ngabo.application.ports.source_replay_repository import SourceReplayRepository
from ngabo.application.ports.verify_reasoning_claims import VerifyReasoningClaims

__all__ = [
    "LoadImportSource",
    "ParseCanonicalSource",
    "ParsedSourceError",
    "ParsedSourceResult",
    "SourceReplayRepository",
    "VerifyReasoningClaims",
]
