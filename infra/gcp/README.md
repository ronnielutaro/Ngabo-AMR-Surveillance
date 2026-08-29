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
- **Full Capability**: Complete regional availability for Cloud Run, Artifact Registry, Firestore Native, Cloud Storage, Pub/Sub, Secret Manager, and Cloud Build.
- **Free Tier Eligibility**: Default location for Google Cloud Free Tier quotas (e.g. Standard Storage).
- **Latency & AI Compatibility**: Broadest feature parity and lowest latency for Google Agent Development Kit (ADK) and Vertex/Gemini endpoints.
- **Zero Cross-Region Egress**: Keeping all compute, storage, and registries within `us-central1` eliminates inter-region networking charges.

---

## 3. Resource Classification Matrix

Every foundation component is strictly classified to preserve boundaries with downstream issues:

| Resource / Service | Classification | Owning Issue | Scope & Notes |
|---|---|---|---|
| **GCP Project** | `CREATE_NOW` | #86 | Creates canonical project boundary (`ngabo-amr-2026`). |
| **Billing Link** | `CREATE_NOW` | #86 | Links project to active Free Trial billing account. |
| **API Allow-list** | `CREATE_NOW` | #86 | Enables the 14 allow-listed Google Cloud APIs. |
| **Artifact Registry** | `CREATE_NOW` | #86 | Provisions Docker repository `ngabo-artifacts` (`us-central1`). |
| **Billing Budget Alerts** | `CREATE_NOW` | #86 | Configures budget monitor alerts at $150, $270, and $300 thresholds. |
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
All resources that support labels must carry:
- `app = ngabo`
- `managed-by = ngabo-bootstrap`
- `lifecycle = hackathon`
- `environment = dev | judge | shared`

### 4.2 Cloud Run Caps Contract (for #90+)
- `min-instances = 0` (Strict scale-to-zero; no idle billable instances)
- `max-instances = 2` (Tight concurrency cap)
- `timeout = 60s` (Bounded request duration)
- `cpu = 1`, `memory = 512Mi`

### 4.3 Storage Lifecycle Contract
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

#### 2. Apply (Idempotent Provisioning)
Provisions missing foundation resources and verifies zero-drift on repeated runs:
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

## 6. Teardown Lifecycle Policy

In alignment with [`docs/CLOUD_COST_AND_TEARDOWN_POLICY.md`](../../docs/CLOUD_COST_AND_TEARDOWN_POLICY.md) §5:
1. **Teardown Order**:
   - Delete container images and Artifact Registry repository.
   - Remove Billing Budget alert from the billing account.
   - Unlink billing account from the project.
   - Submit project shutdown request (`gcloud projects delete`).
2. **Asynchronous Deletion**: Project deletion initiates Google Cloud's 30-day recovery and resource purge lifecycle (`DELETE_REQUESTED`).
3. **Cessation Verification**: Verifies `billingEnabled: false` and confirms no billable traffic or workloads persist.
