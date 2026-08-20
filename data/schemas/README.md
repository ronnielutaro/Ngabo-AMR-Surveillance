# data/schemas

Canonical data schemas for Ngabo data artifacts.

- `canonical_hero.schema.json` — JSON Schema (draft 2020-12) for the
  canonical synthetic hero dataset (M1B.6 / Issue #30). Defines the input
  contract for the hero isolate/AST surveillance observations. Synthetic-only
  by construction: the schema pins `synthetic: true` and requires
  `SYNTH-`-prefixed facility, lab, ward, case and import identifiers. It
  models observations only — no signal, incident, cluster, verification or
  action fields exist in this contract.
