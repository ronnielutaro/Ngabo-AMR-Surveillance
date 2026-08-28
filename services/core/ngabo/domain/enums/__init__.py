"""Domain enums — small framework-free enumerated domain types.

Must never import frameworks, cloud SDKs, AI SDKs, or outer Ngabo layers
(see ``docs/CLEAN_ARCHITECTURE.md``). Populated issue by issue; see Issue #26
for the incident lifecycle state enum (M1B.2), Issue #27 for the
action-class and autonomy-decision-status enums (M1B.3), Issue #28 for
the proof-carrying claim-type enum (M1B.4), Issue #29 for the
claim-verification error-code enum (M1B.5), Issue #38 for the
interpretation and import-validation error-code enums (M2.1),
Issue #40 for the source replay disposition and import deduplication
error-code enums (M2.3), Issue #45 for the resistance profile similarity
status enum (M2.5), Issue #46 for the concentration status and
reason enums (M2.6), and Issue #47 for the signal status and reason enums (M2.7).
"""
