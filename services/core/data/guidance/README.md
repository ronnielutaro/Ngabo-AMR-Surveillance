# data/guidance

Curated approved-evidence corpus (source ID, title, publisher, URL,
date/version) will live here in later milestones. Only retrieved approved
sources may be cited by generated incident packages.

## Current corpus (Issue #51)

This directory now holds the v0.1 approved-evidence corpus:

- `manifest.json` — machine-readable approved-evidence manifest
  (provenance-complete entries, per-source/chunk content digests, and a
  deterministic corpus SHA-256 digest). Schema:
  `data/schemas/evidence_manifest.schema.json`.
- `corpus/` — the committed local content backing each approved chunk. All
  content is a clearly marked **Ngabo-authored retrieval/indexing summary**;
  no full third-party guidance text is redistributed. Each chunk's declared
  `content_sha256` is verified against these bytes before retrieval.

Runtime retrieval is fully local and deterministic (`EvidenceSearchPort`
adapter). Only a source that is approved, version-valid, and integrity-valid
may be returned as reasoning/action-relevant authority. Unapproved sources
(e.g. `UNKNOWN-PUBLISHER-001`) may appear in the manifest for provenance but
can never be retrieved.
