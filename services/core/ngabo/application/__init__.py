"""Ngabo application layer — use cases, workflows, and ports.

Owns commands/queries, application DTOs, agent-facing contracts, and
review/notification gating policy.

May depend on ``ngabo.domain``. Must not import concrete infrastructure
adapters or framework/vendor SDKs.

Populated issue by issue; see Issue #29 for the first application port
contract (M1B.5).
"""
