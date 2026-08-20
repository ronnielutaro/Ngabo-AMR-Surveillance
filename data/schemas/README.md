# data/schemas

Canonical data schemas for Ngabo data artifacts.

- `canonical_hero.schema.json` — JSON Schema (draft 2020-12) for the
  canonical synthetic hero dataset (M1B.6 / Issue #30). Defines the input
  contract for the hero isolate/AST surveillance observations. Synthetic-only
  by construction: the schema pins `synthetic: true` and requires
  `SYNTH-`-prefixed facility, lab, ward, case and import identifiers. It
  models observations only — no signal, incident, cluster, verification or
  action fields exist in this contract.

## Contract invariants

- **Single source of truth for antimicrobial identity:** the `ast_results`
  map key is the antimicrobial code; each entry carries only the observation
  itself (`interpretation`). Entries are `additionalProperties: false`, so a
  duplicated nested identity field is rejected structurally.
- **`isolate_id` uniqueness (documented semantic invariant):** every
  `isolate_id` MUST be unique within one canonical dataset. Plain JSON
  Schema draft 2020-12 cannot naturally express per-property uniqueness
  across an array, so this invariant is documented rather than
  schema-encoded. The committed golden fixture satisfies it; deterministic
  enforcement belongs to the import/dedup boundary in Sprint 2 (Issue #40).
