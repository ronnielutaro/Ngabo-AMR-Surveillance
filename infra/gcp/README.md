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

---

## 7. Identity & Workload Identity Federation Runbook (Issue #87)

The identity management script is located at [`infra/gcp/identity.py`](file:///d:/code/Ngabo-Antimicrobial-Resistance-Surveillance/infra/gcp/identity.py).

### 7.1 Identity Topology & Least Privilege Contracts

1. **`ngabo-deployer`**:
   - **Role**: Dedicated deployment service identity used exclusively by GitHub Actions delivery workflows.
   - **Allowed Project Roles**: **None** (`roles/run.developer` is explicitly deferred to Issue #90 to maintain strict least privilege).
   - **Allowed Resource Roles**: `roles/artifactregistry.writer` on repository `ngabo-artifacts` only (Issue #89: repository-scoped publishing; writer subsumes the former #87-era reader authority, which is revoked on convergence).
   - **Allowed actAs Targets**: `roles/iam.serviceAccountUser` on `ngabo-core-runtime` and `ngabo-web-runtime` only.
   - **Impersonation**: Keyless OIDC federated via Workload Identity Pool `ngabo-github` and Provider `ngabo-repo`.
   - **User-Managed Keys**: **0** (strictly prohibited).

2. **`ngabo-core-runtime` & `ngabo-web-runtime`**:
   - **Role**: Dedicated runtime service identities for future Cloud Run services.
   - **Project Roles**: **None** (zero speculative project-level roles at initial foundation).
   - **User-Managed Keys**: **0** (strictly prohibited).

3. **Deferred Identities**:
   - `event-publisher` and `acknowledger` are explicitly deferred until their actual deployable runtimes are implemented.

### 7.2 Workload Identity Federation (WIF) Trust Contract

- **Pool ID**: `ngabo-github`
- **Provider ID**: `ngabo-repo`
- **Issuer**: `https://token.actions.githubusercontent.com`
- **Immutable Numeric Claims**:
  - `attribute.repository_id = assertion.repository_id` (`1333677446`)
  - `attribute.repository_owner_id = assertion.repository_owner_id` (`29591720`)
- **Attribute Condition**:
  ```cel
  assertion.repository_id == "1333677446" && assertion.repository_owner_id == "29591720" && assertion.ref == "refs/heads/develop" && assertion.environment == "dev"
  ```
- **GitHub Environment Restriction**:
  - Environment: `dev` (restricted to deployment branch `develop`).
- **Pinned Proof Actions**:
  - `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1` (`v7.0.1`)
  - `google-github-actions/auth@7c6bc770dae815cd3e89ee6cdf493a5fab2cc093` (`v3.0.0`)
  - `google-github-actions/setup-gcloud@aa5489c8933f4cc7a4f7d45035b3b1440c9c10db` (`v3.0.1`)

### 7.3 Identity CLI Commands

```bash
# Evaluate live identity, WIF, and GitHub environment state against contract
python infra/gcp/identity.py plan

# Idempotently provision service accounts, WIF pool/provider, and IAM bindings
python infra/gcp/identity.py apply

# Validate that all service accounts exist with 0 keys, WIF matches contract, and no unapproved roles exist
python infra/gcp/identity.py validate

# Run bounded ephemeral synthetic Secret Manager policy probe
python infra/gcp/identity.py secret-probe

# Perform plan-only identity teardown rehearsal
python infra/gcp/identity.py teardown --dry-run
```

---

## 8. Secret Manager Governance Contract (Issue #87)

- **Naming Convention**: `ngabo-dev-<purpose>` and `ngabo-judge-<purpose>`
- **Access Policy**: Resource-scoped `roles/secretmanager.secretAccessor` granted only to owning runtime identities (`ngabo-core-runtime`). Deployer does not receive secret payload access. Project-wide wildcard `roles/secretmanager.secretAccessor` is strictly prohibited.
- **Missing-Secret Policy**: Required secrets must fail fast on application startup with an explicit missing-secret error; silent fallbacks, mock values, and payload logging are forbidden.
- **Physical Secret Boundary**: Zero production secret values are populated in source control or infrastructure code in Issue #87.
