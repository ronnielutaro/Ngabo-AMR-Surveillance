# Ngabo Connect deadline demo

**Status:** implementation artifacts present; the live deployed run must be
executed by the maintainer via `scripts/deadline_demo_bootstrap.ps1` on a
GCP-authenticated machine. This document is the catalog of what is implemented
and the exact reproduction procedure; it does not claim a live run occurred in
this authoring environment.

## Implemented (Epic #171 deadline slice)

- Framework-free Connect contracts: `LaboratorySource`, `SourceProfile`,
  `ConnectBatch`, `AcceptedRecord`, `QuarantinedRecord`, `DataQualityReport`,
  `WorkflowEvent`, `RawSourceIdentity` (`ngabo.application.connect.contracts`).
- Governed source profile `WHONET_DEMO_V1` + deterministic normalizer
  (`ngabo.application.connect.source_profile`). Maps `KPN`/`K pneumoniae` ->
  canonical `kle`/`Klebsiella pneumoniae`; `Resistant`/`Susceptible` -> `R`/`S`;
  `31/08/2026` -> `2026-08-31`. Quarantines unmappable rows.
- Local durable SQLite queue (`ngabo.infrastructure.connect.connect_queue`) with
  SHA-256 de-duplication, restart-safety, bounded exponential backoff.
- HMAC-SHA256 intake verifier (`ngabo.infrastructure.connect.hmac_auth`) verifying
  lab/source, timestamp window, digest, and signature.
- Synthetic fixture `demo/connect/synthetic_gulu_surveillance_export.csv`:
  4 rows -> 3 accepted, 1 quarantined (`UNKNOWN_ORGANISM_CODE` for `KLP???`).
- Idempotent deploy/smoke/launch scripts under `scripts/deadline_demo_*.ps1`.

## Fixture-derived facts

- `received_count=4`, `accepted_count=3`, `quarantined_count=1`,
  `normalization_count=3`.
- The 3 accepted Ward-A `Klebsiella pneumoniae` blood isolates carry the
  carbapenem-resistant phenotype (AMK=S, CAZ/CIP/CRO/MEM/SXT=R), which is the same
  science as the certified hero and deterministically qualifies for an
  investigation-priority signal.

## Reproduction steps

1. On a GCP-authenticated machine run `scripts/deadline_demo_bootstrap.ps1`.
2. Run `scripts/start_ngabo_connect.ps1` to create the watched folder.
3. Launch the edge client
   (`python -m ngabo.infrastructure.connect.edge --watch-dir <dir>`).
4. Copy `demo/connect/synthetic_gulu_surveillance_export.csv` into the watched
   folder.
5. The system automatically detects, queues, syncs, cleans, quarantines, persists,
   refreshes surveillance, detects the signal, runs the existing hero, executes the
   A1 coordination, and verifies the signed receiver ACK.

Zero human workflow actions after the export appears.

## Not claimed

- Live ALIS or hospital integration.
- Real patient data / PHI handling.
- Multi-tenant fleet or device management.
- National-scale architecture.
- A production installer (the desktop client is a Python module, not an .exe).

No secrets, patient data, or chain-of-thought are recorded here.
