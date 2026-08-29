# Ngabo Google Cloud Foundation Runbook (Issue #86)

This document provides the operational runbook and architecture specification for Ngabo's Google Cloud foundation bootstrap, cost boundaries, and teardown procedures.

---

## 1. Governance & Constraints

- **Parent Epic**: [#84 — GCP Foundation and Incremental Delivery Skeleton](https://github.com/ronnielutaro/Ngabo-AMR-Surveillance/issues/84)
- **Active Issue**: [#86 — Cloud Foundation 1A.2: Define environments and automate the GCP bootstrap](https://github.com/ronnielutaro/Ngabo-AMR-Surveillance/issues/86)
- **Governing Policy**: [`docs/CLOUD_COST_AND_TEARDOWN_POLICY.md`](../../docs/CLOUD_COST_AND_TEARDOWN_POLICY.md)
- **Financial Boundary**:
  - `OUT_OF_POCKET_LIMIT_USD = 0` (Strict zero-cash spend)
  - `AUTO_UPGRADE_TO_PAID = false`
  - Free Trial program boundary: `$300.00 USD / 90 days` (Expires November 28, 2026)
  - **Important**: The Cloud Billing budget alert is a notification monitor and **NOT a hard spending cap**. The maintainer Free Trial credits console remains the authoritative source for remaining promotional credits.

---

## 2. Architecture Decisions

### 2.1 Topology: Single Dedicated GCP Project
Ngabo uses **ONE dedicated Google Cloud project** (`ngabo-amr-2026` or configured via `NGABO_GCP_PROJECT_ID`), isolated under a dedicated maintainer Google account.

**Rationale**:
- Eliminates duplicate billing accounts and multi-project Free Trial quota conflicts.
- Reduces cross-project IAM and networking complexity during a rapid hackathon timeframe.
- Cleanly isolates environments using naming prefixes (`dev-`, `judge-`, `shared-`) and resource labels (`environment: dev | judge | shared`).

### 2.2 Primary Region: `us-central1` (Iowa)
All regional services are deployed in `us-central1`.

**Rationale**:
- **Full Service Availability**: Complete regional availability for Cloud Run, Artifact Registry, Firestore Native, Cloud Storage, Pub/Sub, Secret Manager, and Cloud Build.
- **Reference Pricing & Free Tier**: Default location for Google Cloud Free Tier quotas (e.g., Cloud Storage Standard tier and Cloud Run invocation tiers).
- **Regional Co-location**: Co-locating eligible regional compute and storage resources reduces avoidable inter-region data transfer. Future Gemini/Vertex model endpoint placement remains owned by Issue #49.

### 2.3 Firestore Location Contract: `us-central1`
When Firestore is provisioned in future issues, it will use the regional location **`us-central1`**, directly co-located with application compute and container storage, avoiding multi-region replication latency and cost overheads. Database creation remains strictly **DEFERRED**.

---

## 3. Resource Classification Matrix

Every foundation component is strictly classified to preserve boundaries with downstream issues:

| Resource / Service | Classification | Owning Issue | Scope & Notes |
|---|---|---|---|
| **GCP Project** | `CREATE_NOW` | #86 | Creates canonical project boundary (`ngabo-amr-2026`). |
| **Billing Link** | `CREATE_NOW` | #86 | Links project to verified Free Trial billing account. |
| **API Allow-list** | `CREATE_NOW` | #86 | Enables the 14 Ngabo-managed required Google Cloud APIs. |
| **Artifact Registry** | `CREATE_NOW` | #86 | Provisions Docker repository `ngabo-artifacts` (`us-central1`). |
| **Billing Budget Alerts** | `CREATE_NOW` | #86 | Configures budget monitor alerts at $150, $270, $290, and $300 thresholds over the Free Trial window. |
| **Cloud Run API** | `ENABLE_API_ONLY` | #86 | Enables `run.googleapis.com`. Service deployment belongs to #90. |
| **Secret Manager API** | `ENABLE_API_ONLY` | #86 | Enables `secretmanager.googleapis.com`. Secret contracts belong to #87. |
| **Cloud Build API** | `ENABLE_API_ONLY` | #86 | Enables `cloudbuild.googleapis.com`. Build workflows belong to #88/#89. |
| **Firestore API** | `ENABLE_API_ONLY` | #86 | Enables `firestore.googleapis.com`. Schema/rules belong to persistence issue. |
| **Pub/Sub API** | `ENABLE_API_ONLY` | #86 | Enables `pubsub.googleapis.com`. Event topic contracts belong to messaging issue. |
| **Cloud Storage API** | `ENABLE_API_ONLY` | #86 | Enables `storage.googleapis.com`. Application buckets are deferred. |
| **IAM & WIF** | `DEFER` | #87 | Service accounts and Workload Identity Federation strictly belong to #87. |
| **Container Images** | `DEFER` | #89 | Building and publishing immutable container images belongs to #89. |
| **Cloud Run Services** | `DEFER` | #90 | Deploying `ngabo-core` and `ngabo-web` skeleton services belongs to #90. |

---

## 4. Governed Resource Constraints

### 4.1 Labels
All foundation resources must carry the standard label set:
- `app = ngabo`
- `managed-by = ngabo-bootstrap`
- `lifecycle = hackathon`
- `environment = shared` (or `dev` / `judge` for environment-specific resources)
- `owner = ngabo-maintainer`

### 4.2 Free Trial Budget Contract
- **Scope**: Filtered specifically to the canonical Ngabo project (`projects/ngabo-amr-2026`).
- **Amount**: `$300.00 USD`.
- **Time Window**: Custom period from Free Trial activation (`2026-08-29`) to expiration (`2026-11-28`).
- **Credit Treatment**: `EXCLUDE_ALL_CREDITS` so promotional Free Trial credits do not conceal underlying resource consumption from alert rules.
- **Threshold Rules**:
  - `50%` ($150.00) Current Spend
  - `90%` ($270.00) Current Spend
  - `96.67%` (~$290.00) Current Spend (Early warning boundary before $10 teardown reserve)
  - `100%` ($300.00) Current Spend
  *(Note: The Billing Budgets API does not permit forecasted-spend rules on custom-period budgets).*

### 4.3 Cloud Run Caps Contract (for #90+)
- `min-instances = 0` (Strict scale-to-zero; no idle billable instances)
- `max-instances = 2` (Tight concurrency cap)
- `timeout = 60s` (Bounded request duration)
- `cpu = 1`, `memory = 512Mi`

### 4.4 Storage Lifecycle Contract
- Default lifecycle rule: Automatically delete ephemeral build/test objects older than 7 days.
- Public access prevention: `enforced`.

---

## 5. Bootstrap CLI Usage

The bootstrap script is located at [`infra/gcp/bootstrap.py`](file:///d:/code/Ngabo-Antimicrobial-Resistance-Surveillance/infra/gcp/bootstrap.py).

### Prerequisites
1. Local `gcloud` CLI installed and authenticated (`gcloud auth login`).
2. Maintainer account enrolled in Google Cloud Free Trial.
3. Python 3.11+ available.

### Commands

#### 1. Plan (Non-mutating)
Inspects live GCP state against desired configuration and displays pending actions:
```bash
python infra/gcp/bootstrap.py plan
# Or with json format:
python infra/gcp/bootstrap.py plan --format=json
```

#### 2. Apply (Idempotent Provisioning & Reconciliation)
Provisions missing foundation resources, reconciles mutable label/budget drift, and verifies zero-drift on repeated runs:
```bash
python infra/gcp/bootstrap.py apply
```

#### 3. Validate
Verifies live state against the committed allow-list and checks all governance assertions:
```bash
python infra/gcp/bootstrap.py validate
```

#### 4. Teardown Rehearsal (Dry Run)
Rehearses the teardown sequence without modifying active cloud resources:
```bash
python infra/gcp/bootstrap.py teardown --dry-run
```

---

## 6. Teardown Lifecycle & Rehearsal Semantics

The `teardown --dry-run` command performs a **plan-only rehearsal** (`teardown_mode = PLAN_ONLY`). It does **not** execute destructive operations, does **not** disable billing, and does **not** initiate project deletion.

When a **real** teardown is explicitly authorized by the maintainer:
1. **Teardown Sequence**:
   - Delete container images and Artifact Registry repository (`ngabo-artifacts`).
   - Remove Billing Budget alert from the billing account.
   - Unlink billing account from the project (`gcloud billing projects unlink`).
   - Submit project shutdown request (`gcloud projects delete`).
2. **Cessation Verification**:
   - Verify `billingEnabled: false`.
   - Confirm project lifecycle state transitions to `DELETE_REQUESTED`.
   - Verify zero billable active workloads remain.
