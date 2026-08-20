# data/synthetic

Synthetic demonstration datasets (WHONET-style fixtures).

- `canonical_hero.json` — the canonical Taskmaster hero fixture (M1B.6 /
  Issue #30), validating against `../schemas/canonical_hero.schema.json`.
  Eight synthetic isolate/AST surveillance observations authored for Ngabo:
  three Ward A Klebsiella pneumoniae records (`ISO-031`, `ISO-034`,
  `ISO-039`) plus five contrast records for baseline/similarity context.
  Observations only: the fixture carries no derived signal, incident or
  action facts. All eight `isolate_id` values are unique, satisfying the
  dataset-level uniqueness invariant documented in `../schemas/README.md`
  (deterministic enforcement is owned by Issue #40).

Every fixture must be explicitly labelled as synthetic; no real patient,
hospital, or laboratory data may ever be committed.
