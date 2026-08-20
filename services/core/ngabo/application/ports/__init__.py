"""Application ports — inward-facing framework-free contracts.

Ports here are Protocols that application workflows depend on and outer
layers (interfaces/infrastructure) implement; see
``docs/CLEAN_ARCHITECTURE.md``. May depend on ``ngabo.domain`` only. Must
never import framework/vendor SDKs or outer Ngabo layers.

Populated issue by issue; see Issue #29 for the claim-verification port
(M1B.5).
"""
