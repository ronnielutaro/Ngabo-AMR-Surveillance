# Security Policy

Ngabo is currently a **hackathon prototype using synthetic demonstration data only**. It is not approved for real clinical, patient-identifiable, or production hospital data.

## Supported Scope

During v0.1 development, security work focuses on:

- keeping credentials and API keys out of source control;
- using Secret Manager / Cloud Run secret injection for deployed secrets;
- treating uploaded laboratory fields as untrusted data;
- preventing prompt injection from uploaded content from becoming runtime instructions;
- keeping runtime agent tools narrowly scoped;
- validating structured model outputs;
- preventing duplicate side effects from Pub/Sub retries;
- preserving an auditable incident event trail;
- using synthetic data in tests, screenshots, logs, and demos.

## Do Not Use Real Patient Data

Do not upload, commit, log, or test with:

- patient names;
- medical record numbers;
- real identifiable laboratory records;
- other protected or sensitive clinical data.

A future real-world deployment would require a separate privacy, security, clinical-governance, access-control, retention, encryption, legal, and regulatory review.

## Reporting a Vulnerability

Please use GitHub's private security-advisory mechanism for this repository when available rather than posting exploitable details in a public issue.

Include:

- affected component;
- reproduction steps;
- expected vs actual behavior;
- potential impact;
- suggested mitigation if known.

## Runtime Agent Security Boundary

The Ngabo runtime agent must not receive unrestricted shell access, unrestricted database mutation, or arbitrary web browsing merely for convenience. Runtime tools should be typed, scoped, and auditable.

See `CLAUDE.md`, `AGENTS.md`, and `docs/DATA_SAFETY_EVALUATION.md` for the full implementation contract.
