# Ngabo — Cloud Cost, Privacy, and Teardown Policy

**Status:** Governed Cloud Boundary Contract  
**Version:** 1.1  
**Date:** 2026-08-29  
**Issue Reference:** #85 (Cloud Foundation 1A.1)  
**Parent Epic:** #84 (Epic 1A: GCP Foundation and Incremental Delivery Skeleton)  

---

## 1. Objective and Scope

This document defines the maintainer-owned cloud account, cost, privacy, and teardown boundaries for the Ngabo Antimicrobial Resistance Surveillance hackathon deployment.

It establishes strict operational boundaries prior to any infrastructure provisioning in Issue #86, ensuring that:
1. Cloud resources reside in a dedicated, isolated Google Cloud environment.
2. The funding source is strictly bounded to confirmed Google Cloud Free Trial credits and ongoing Free Tier allowances.
3. Out-of-pocket cash spend is capped at **$0 USD**.
4. No sensitive credentials, payment cards, billing account IDs, or personal verification artifacts enter Git history or public issues.
5. All future cloud infrastructure is subject to automated teardown triggers and scale-to-zero discipline.

---

## 2. Dedicated Account & Free Trial Eligibility Policy

### 2.1 Account Isolation
Ngabo utilizes a newly created Google account dedicated exclusively to this hackathon environment.
- **Purpose**: Clean ownership isolation, separate billing and usage reporting, simplified least-privilege IAM management, and unambiguous post-hackathon environment teardown.
- **No Circumvention Guarantee**: A new account is established strictly for isolation. It does not alter or evade Google Cloud's official Free Trial eligibility requirements.

### 2.2 Verified Free Trial Boundary
The dedicated account underwent official Google Cloud Free Program enrollment and verification on **2026-08-29**:

| Parameter | Governed Value / Status | Verification Notes |
|---|---|---|
| **Eligibility & Status** | `ELIGIBLE_AND_ACTIVATED` | Confirmed live in Google Cloud Console |
| **Initial Trial Credit** | `$300.00 USD` | $0.00 consumed at initialization |
| **Trial Duration / Expiry** | 90 days (Expires November 28, 2026) | Full coverage through hackathon judging window |
| **Automatic Billing Upgrade** | `DISABLED` | Upgrading to paid billing requires manual maintainer action |
| **Billing Ownership** | Maintainer-owned | Managed directly by project maintainer |

---

## 3. Three-Tier Cost Boundary

To ensure complete cost predictability, Ngabo distinguishes three separate usage layers:

### 3.1 Tier 1: Free Trial Credits ($300 USD)
- Represents the **primary hackathon development and testing budget**.
- Applied automatically by Google Cloud to eligible services during the 90-day active window.
- Covers ephemeral Cloud Run compute, container builds, temporary storage, and live demonstration endpoints.

### 3.2 Tier 2: Google Cloud Free Tier

Google Cloud provides service-specific free usage allowances that may apply during and after the Free Trial.

These limits are not governed constants in Ngabo because Google may change them and some vary by region, billing mode, edition, or billing account.

Before provisioning or changing any billable service, the owning issue must:

1. re-check the current official Google Cloud pricing/free-tier documentation;
2. record the relevant service, region, billing mode, and observed free allowance;
3. configure explicit cost/usage controls appropriate to that service;
4. preserve the project-wide `OUT_OF_POCKET_LIMIT_USD = 0` boundary.

Free Tier allowances are an optimization, not Ngabo's primary safety control.

### 3.3 Tier 3: Out-of-Pocket Paid Spend Boundary
- **Approved Limit**: `OUT_OF_POCKET_LIMIT_USD = 0` (Strict maintainer-authorized zero-cash spend).
- **Auto-Upgrade Policy**: `AUTO_UPGRADE_TO_PAID = false`.
- **Policy Enforcement**: The Google Cloud Billing account remains in un-upgraded Free Trial mode. If trial credits expire or are depleted, services pause rather than incurring credit card charges.

---

## 4. Fallback Policy

If Free Trial credits are exhausted, expire, or become restricted:

1. Ngabo must not automatically upgrade to paid billing.
2. The certified deterministic offline core remains available for local testing, replay, scientific verification, and development continuity.
3. The offline core is NOT a substitute for the Google Cloud / Google agent framework / Gemini requirements of the hackathon submission.
4. If the required Google Cloud backend and deployment evidence cannot be restored within the approved zero-cash boundary before submission freeze, the condition is treated as a submission blocker.
5. Submission materials must never imply cloud execution occurred when only local/offline execution was available.

---

## 5. Teardown Triggers & Lifecycle Policy

All cloud resources created in Issue #86 and subsequent infrastructure milestones must be designed for rapid, reproducible deletion.

### 5.1 Mandatory Teardown Triggers
Resources in the dedicated Google Cloud environment must be destroyed/disabled upon any of the following events:
1. **Submission Freeze & Judging Conclusion**: Hackathon judging finishes and frozen evidence is archived.
2. **Credit Threshold**: Remaining Free Trial credit drops below `$10.00 USD`.
3. **Expiry Proximity**: Active trial approaches within 7 days of expiration (November 21, 2026).
4. **Unexpected Billing**: Any non-zero charges or billing anomalies are observed.
5. **Project Abandonment / Maintainer Discretion**: The maintainer explicitly calls for environment destruction.

### 5.2 Teardown Mechanism

Later infrastructure issues must provide an explicit, reproducible teardown procedure for Ngabo-managed resources.

The preferred sequence is:

1. stop externally reachable workloads;
2. disable or detach billing where appropriate;
3. delete or disable explicitly managed resources through the governed infrastructure/runbook;
4. verify that traffic, background execution, and billable usage have stopped;
5. optionally shut down the dedicated GCP project as the final environment-level action.

Google Cloud project shutdown is not treated as an instantaneous atomic resource deletion primitive. Project shutdown moves the project into Google's deletion lifecycle and associated resources can have service-specific deletion and recovery behavior.

Final teardown evidence must verify lifecycle state and billing/traffic cessation rather than merely proving that a delete command was submitted.

---

## 6. Cost-Control Invariants for Later Infrastructure Issues

Issues #86 through #92 must strictly uphold the following constraints:

1. **Scale to Zero**: All Cloud Run services (`ngabo-core`, `ngabo-web`) must set `min-instances = 0`. No always-on compute instances or unbudgeted idle processes are permitted.
2. **Strict Instance Caps**: Cloud Run services must enforce a low `max-instances` cap (default `max-instances = 2`).
3. **Bounded Request Timeouts**: HTTP request timeouts must be bounded (e.g. 60 seconds) to prevent hung executions from consuming compute quotas.
4. **Bounded Storage & Retention**:
   - Cloud Storage buckets must configure object lifecycle rules (deleting ephemeral objects after 7 days).
   - Firestore and Pub/Sub retention must be minimized.
   - Cloud Logging retention must be constrained to the default standard period.
5. **Resource Labeling**: All provisioned GCP resources must carry standardized attribution labels (`project:ngabo`, `environment:hackathon`, `managed-by:opentofu-or-gcloud`).
6. **Keyless Identity**: GitHub Actions deployment must utilize Workload Identity Federation (WIF). Storing long-lived service account JSON keys in GitHub Secrets is strictly prohibited.
7. **Canonical Project Boundary**: The Google-created signup placeholder project (identifier intentionally omitted) is an account-creation artifact only. Issue #86 will establish the canonical project hierarchy.

---

## 7. Privacy and Secret Sanitization Audit

In accordance with repository privacy standards:
- **No Credentials Committed**: No passwords, recovery phone/email addresses, SMS codes, or OAuth tokens are present in this repository.
- **No Billing Identifiers**: The internal Cloud Billing Account ID and payment card identifiers are strictly redacted from all public documentation and commit history.
- **Audit Result**: Clean.
