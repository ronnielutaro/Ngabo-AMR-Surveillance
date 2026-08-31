# Ngabo Connect demo fixture — Synthetic Surveillance Lab — Gulu

This is a **synthetic**, governed, WHONET-style laboratory export.

- It is **not** real patient data and does **not** represent Gulu Regional Referral
  Hospital or any real facility.
- Source profile: `WHONET_DEMO_V1`.
- It intentionally uses *messy* source representation that the deterministic
  normalizer maps to canonical codes:
  - `KPN` -> canonical organism code `kle`; `K pneumoniae` -> `Klebsiella pneumoniae`.
  - `Resistant` / `Susceptible` -> `R` / `S`.
  - `31/08/2026` -> `2026-08-31`.
- Expected outcome:
  - received_count = `4`
  - accepted_count = `3`
  - quarantined_count = `1`
  - normalization_count = `3`
- The quarantined row (`WHN-099`, organism `KLP???`) is rejected with
  `UNKNOWN_ORGANISM_CODE` and is structurally excluded from surveillance.
- The 3 accepted Ward-A `Klebsiella pneumoniae` blood isolates with the
  carbapenem-resistant phenotype are the same science as the certified hero
  fixture and deterministically produce an investigation-priority signal.

No live ALIS or hospital integration. Surveillance thresholds are unchanged.
