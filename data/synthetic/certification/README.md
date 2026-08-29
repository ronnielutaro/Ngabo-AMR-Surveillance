# Synthetic Certification Scenario Fixtures

This directory contains durable, committed synthetic CSV fixtures used to certify the offline hero surveillance pipeline release gate (Issue #48 / M2.8).

All data are purely synthetic demonstrations; no real patient, hospital, or clinical data are present.

## Fixture Manifest

- `normal_baseline.csv` — Routine sporadic surveillance observations across multiple facilities/wards with susceptible isolates and cluster sizes $k < 3$. Certified result: `execution_succeeded = true`, `certified = false`, `signal_count = 0`.
- `malformed_header.csv` — Syntactically invalid CSV structure missing mandatory WHONET surveillance columns. Certified result: `execution_succeeded = false`, `certified = false`, `errors = [PARSER_FAILURE]`.
- `conflicting_duplicate.csv` — Duplicate isolate records sharing the same `ISOLATE_ID` but with conflicting AST measurements. Certified result: `execution_succeeded = false`, `certified = false`, `errors = [CONFLICTING_DUPLICATE_RECORD]`.
- `missing_phenotype_evidence.csv` — Isolate records with uninterpretable or missing AST phenotype measurements ($c_{pheno} = \text{INSUFFICIENT\_DATA}$). Certified result: `execution_succeeded = true`, `certified = false`, `signal_count = 0`.
- `prompt_injection.csv` — Synthetically valid CSV containing adversarial prompt-injection payloads in string fields, proving deterministic immunity. Certified result: `execution_succeeded = true`, `certified = false`, `signal_count = 0`.
- `material_change.csv` — Materially altered version of the canonical hero fixture (7 isolates instead of 8). Certified result: `execution_succeeded = true`, `certified = false`, `import_disposition = MATERIAL_CHANGE`.
- `canonical_hero_reordered.csv` — Exact 8 rows of `canonical_hero.csv` with permuted/reversed row ordering, proving row-order invariance yielding identical canonical source watermark, signal ID, and event ID.
