"""Domain services — deterministic framework-free domain policy.

Must never import frameworks, cloud SDKs, AI SDKs, or outer Ngabo layers
(see ``docs/CLEAN_ARCHITECTURE.md``). Populated issue by issue; see Issue #26
for the incident transition policy added in M1B.2, Issue #38 for the
deterministic canonical import-boundary validation added in M2.1,
Issue #40 for deterministic source identity, artifact digest, canonical
watermarking, and import deduplication added in M2.3, and Issue #45
for deterministic resistance profile similarity evaluation added in M2.5.
"""
