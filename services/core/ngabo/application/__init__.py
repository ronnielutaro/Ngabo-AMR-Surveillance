"""Ngabo application layer — use cases, workflows, and ports.

Owns commands/queries, application DTOs, agent-facing contracts, and
review/notification gating policy.

May depend on ``ngabo.domain``. Must not import concrete infrastructure
adapters or framework/vendor SDKs.

Populated issue by issue:
- Issue #29: ``VerifyReasoningClaims`` port contract (M1B.5).
- Issue #44: Canonical import orchestration use case, ports, commands, and results (M2.4).
- Issue #48: Offline hero surveillance certification use case and result (M2.8).
"""

from __future__ import annotations
