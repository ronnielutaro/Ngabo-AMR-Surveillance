# Reproducing Ngabo v0.1

**Scope:** synthetic hackathon Connect-to-coordination slice

**Public dashboard:** <https://ngabo-web-2zhvmdaotq-uc.a.run.app/>

This runbook separates three different claims that must not be confused:

1. **Repository reproduction:** install locked dependencies, run tests and build the artifacts.
2. **Local edge reproduction:** exercise the desktop watcher, durable queue, signing and acknowledgement without cloud credentials.
3. **Deployed hero reproduction:** run the real Firestore + Google ADK + Gemini + signed Cloud Run receiver path with authorized GCP access.

Passing repository tests does not establish a deployed run. An HTTP 200 does not establish hero completion. The deployed hero is proven only when the result reaches `HERO_COMPLETED`, includes a verified machine acknowledgement, and records zero human workflow actions.

## 1. Reproduction Matrix

| Capability | No cloud credentials | Authorized Ngabo GCP maintainer | Independent fork owner |
| --- | --- | --- | --- |
| Install and build | Yes | Yes | Yes |
| Deterministic and safety test suites | Yes | Yes | Yes |
| Desktop queue/HMAC flow against local intake | Yes | Yes | Yes |
| Public dashboard viewing | Yes | Yes | Yes |
| Private core status/intake | No | Yes | Only in the fork's project |
| Real Firestore/Gemini hero | No | Yes | Yes, after creating equivalent resources |
| Publish/deploy through repository WIF | No | Yes | Requires fork-specific WIF/IAM changes |

## 2. Clean Checkout

Prerequisites:

- Git;
- Node.js 20+;
- Corepack and `pnpm@11.22.0`;
- Python 3.11+;
- [uv](https://docs.astral.sh/uv/);
- Docker for container reproduction;
- Google Cloud CLI for cloud reproduction.

```bash
git clone https://github.com/ronnielutaro/Ngabo-AMR-Surveillance.git
cd Ngabo-AMR-Surveillance
corepack enable
corepack prepare pnpm@11.22.0 --activate
pnpm install --frozen-lockfile
uv sync --project services/core --frozen
```

Use the submitted tag or commit once the release freeze is published. Do not assume a later mutable branch head is the judged artifact.

## 3. Repository Verification

```bash
pnpm web:lint
pnpm web:typecheck
pnpm web:test
pnpm web:build
pnpm core:lint
pnpm core:typecheck
pnpm core:test
pnpm core:architecture
```

Expected result: every command exits zero. The suites include deterministic Connect/scientific behavior, typed proof validation, A2/A3 blocking, idempotency/freshness behavior and zero-human hero composition. These are software checks, not clinical validation.

## 4. Local Desktop Edge Reproduction

Start the local intake emulator:

```bash
uv run --project services/core python scripts/local_connect_intake.py
```

Launch the desktop client against it.

PowerShell:

```powershell
$env:NGABO_INTAKE_URL = "http://127.0.0.1:8099/connect/batches"
uv run --project services/core python scripts/ngabo_connect_desktop.py
```

macOS/Linux:

```bash
NGABO_INTAKE_URL=http://127.0.0.1:8099/connect/batches \
  uv run --project services/core python scripts/ngabo_connect_desktop.py
```

Then:

1. choose an empty watched folder;
2. click **Start Watching**;
3. copy `demo/connect/synthetic_gulu_surveillance_export.csv` into that folder;
4. confirm that the window logs `DETECTED` and then `ACKNOWLEDGED`;
5. restart the desktop client and confirm an acknowledged file is not duplicated.

This proves only the edge boundary: file stability, SHA-256 identity, SQLite durability, HMAC signing, retries and acknowledgement. The local intake emulator does not claim to execute Firestore, Gemini or external safe coordination.

## 5. Deployed Topology

The submitted deployment uses:

| Component | Runtime boundary |
| --- | --- |
| `ngabo-web` | Public Cloud Run service; server-side dashboard |
| `ngabo-core` | Private Cloud Run service; Connect intake, deterministic pipeline and hero composition |
| `ngabo-demo-receiver` | Cloud Run synthetic A1 signed-delivery endpoint |
| Firestore database `ngabo` | Canonical isolates, incidents, workflow state and ActionIntents |
| Secret Manager | Gemini API credential injected into `ngabo-core` |
| Artifact Registry | Immutable core/web container images |
| Cloud Logging | Runtime and platform telemetry |

The browser does not call the private core directly. `ngabo-web-runtime` has service-level `roles/run.invoker` on `ngabo-core`. The desktop client obtains an audience-bound ID token by impersonating the narrow `ngabo-connect-demo` invoker identity and also HMAC-signs the batch.

See the [deployed architecture diagram](./ARCHITECTURE_DIAGRAM.md).

## 6. Required Core Runtime Contract

The deployed hero needs the following configuration. Values marked secret must come from Secret Manager or another non-committed secret mechanism.

| Variable | Purpose |
| --- | --- |
| `NGABO_GCP_PROJECT` | Firestore/project binding |
| `NGABO_HERO_ADAPTER_REGISTRY=ngabo.bootstrap.hero_registry` | Loads the real investigation/model/action adapters |
| `NGABO_RECEIVER_URL` | Authorized signed receiver URL |
| `NGABO_ACK_SECRET` | Shared synthetic acknowledgement verification secret |
| `NGABO_HMAC_SECRET` | Connect batch signature secret |
| `NGABO_SURVEILLANCE_WINDOW_END` | Deterministic synthetic demo window |
| `NGABO_ADK_MODEL=gemini-3.6-flash` | Governed model identifier |
| `NGABO_ENVIRONMENT` | Runtime environment label |
| `NGABO_IMAGE_DIGEST` | Immutable deployed core artifact identity |
| `GEMINI_API_KEY` / `GOOGLE_API_KEY` | Secret Manager references to the Gemini credential |

Never commit, print or place real keys directly in a deployment command. The public demo secrets used for synthetic HMAC/acknowledgement proof are not production credentials and must not be reused for real integrations.

## 7. Cloud Foundation and Delivery

The checked-in automation is the source of truth for this repository's existing project:

```bash
pnpm infra:plan
pnpm infra:validate
pnpm infra:identity:plan
pnpm infra:identity:validate
```

The mutating `infra:apply` and `infra:identity:apply` commands require explicit billing/IAM authority. Review their plans before applying them.

Container and Cloud Run delivery uses:

- `.github/workflows/publish-containers.yml` for keyless build, test, scan and immutable publication;
- `.github/workflows/deploy-cloudrun.yml` / `.github/workflows/delivery-develop.yml` for private-core/public-web deployment by digest;
- `infra/gcp/cloudrun.py` as the core/web desired-state implementation;
- `.github/workflows/promote-cloudrun.yml` for protected no-rebuild promotion.

### Project portability boundary

The existing workflows and some GCP constants are intentionally bound to `ronnielutaro/Ngabo-AMR-Surveillance` and `ngabo-amr-2026`. A fork owner must provide a new project, billing account, Artifact Registry repository, Firestore database, Secret Manager secret, service accounts, GitHub environments and WIF provider, then replace the repository/project identity constants before applying anything.

The current generic core/web Cloud Run desired-state script configures the service skeleton and identity boundary. The hero-specific receiver and runtime variables above must also be present for the full Connect hero. Treat missing hero configuration as a failed reproduction even if `/health` succeeds.

## 8. Real Cloud E2E

For an authorized maintainer with `gcloud` application credentials and `GEMINI_API_KEY` available only in the process environment:

```bash
uv run --project services/core python scripts/deadline_demo_e2e_smoke.py
```

Required completion evidence:

```text
outcome             HERO_COMPLETED
ack_verified        true
delivery_id         non-empty
ack_id              non-empty
manual prompts      0
human interventions 0
human active steps  0
clarifications      0
approval clicks     0
E2E_RESULT          HERO_COMPLETED
```

A `BLOCKED`, `VALIDATION_FAILED`, `POLICY_BLOCKED` or other abstention outcome demonstrates fail-closed behavior, but it does not satisfy the positive hero-completion gate.

## 9. Deployed Desktop-to-Dashboard Demonstration

For an authorized maintainer:

1. confirm the public dashboard loads and does not report `core unreachable`;
2. confirm an unauthenticated call to the private core returns `403`;
3. launch `uv run --project services/core python scripts/ngabo_connect_desktop.py`;
4. choose a new empty folder and start watching;
5. copy the committed synthetic fixture into the folder;
6. observe `DETECTED` and `ACKNOWLEDGED` in the desktop client;
7. observe the persisted counts and signal on the public dashboard;
8. require `HERO COMPLETED`, a delivery ID, a machine acknowledgement ID and zero-human counters before claiming success.

Do not use real patient data, hospital credentials or real-person notification targets in this v0.1 demonstration.

## 10. Known Boundaries

- Synthetic data only.
- No production ALIS/WHONET/LIS/LIMS connector.
- No clinical validation or autonomous clinical/official decision.
- The desktop client is a Python/Tkinter demo client, not a signed production installer.
- Pub/Sub and Cloud Storage are broader roadmap components and are not claimed as exercised in the direct Connect path.
- A clean third-party GCP deployment is documented but not yet packaged as portable Terraform or a one-command installer.
