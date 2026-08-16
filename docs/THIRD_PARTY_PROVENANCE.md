# Ngabo — Third-Party Provenance, Licensing & Pre-Existing Work Register

**Status:** Required v0.1 submission-compliance contract  
**Date:** 2026-08-16

---

## 1. Purpose

The hackathon requires entrants to be authorized to use third-party SDKs, APIs, data, and other information in accordance with applicable terms/licensing requirements. It also requires disclosure of non-standard pre-existing code or work incorporated into the project.

Ngabo therefore maintains this register as a release/submission gate.

This document is not legal advice. It is an engineering provenance record used to make licensing, attribution, ownership, and submission disclosures explicit before release.

---

## 2. General Rules

Before any third-party component/data/source is included in the submitted build:

1. identify the component/source;
2. record where it came from;
3. record the applicable license/terms or usage basis;
4. record how Ngabo uses it;
5. record whether redistribution is occurring;
6. satisfy required attribution/notices;
7. verify that the use is compatible with the public repository and hackathon submission;
8. do not include material whose usage basis is unclear.

If authorization cannot be established, remove or replace the dependency/data before submission.

---

## 3. Software / Service Register

Populate exact versions and links during implementation.

| Component / service | Intended role | Source | License / terms status | Redistribution? | Submission status |
|---|---|---|---|---|---|
| Google ADK Python | Agent graph/runtime | Official Google distribution/repository | Verify exact installed-version license/terms and retain notices | Package dependency only | REQUIRED — pending version capture |
| Gemini API / `gemini-3.6-flash` | Bounded agent reasoning | Google Gemini API | Use under applicable Google API/service terms | No model redistribution | REQUIRED — pending deployed proof |
| Google Cloud Run | Web/core hosting | Google Cloud | Google Cloud service terms | No | REQUIRED — pending deploy |
| Firestore | Canonical workflow persistence | Google Cloud | Google Cloud service terms | No | REQUIRED — pending deploy |
| Pub/Sub | Event transport | Google Cloud | Google Cloud service terms | No | REQUIRED — pending deploy |
| Cloud Storage | File/artifact storage | Google Cloud | Google Cloud service terms | No | REQUIRED — pending deploy |
| Cloud Logging / tracing | Operational proof/observability | Google Cloud | Google Cloud service terms | No | REQUIRED — pending deploy |
| EmbeddingGemma | Approved-corpus semantic retrieval | Official Google model distribution | Verify model license/terms for selected distribution before merge | Model weights must not be committed unless terms clearly permit and repository policy approves | PLANNED — gated |
| MedGemma | Optional bounded evidence interpretation | Official Google Health AI distribution | Verify selected model license/terms before integration | Do not commit weights by default | OPTIONAL — gated |
| Next.js / React / FastAPI / Pydantic / other packages | Application framework/dependencies | Official package registries/upstream repos | Capture through lockfiles and generated notices/license inventory | Dependency distribution as permitted by applicable licenses | REQUIRED as used |

This table is a control surface, not proof by itself. Exact versions/links should be copied into the final submission evidence and dependency lockfiles.

---

## 4. WHONET Compatibility / Input Data Boundary

Ngabo v0.1 uses **synthetic WHONET-style tabular microbiology data** for demonstration.

Rules:

- do not redistribute WHONET application binaries/source unless explicitly authorized and required;
- do not imply WHO/WHONET sponsorship or endorsement;
- do not package real WHONET patient/laboratory exports in the public repository;
- synthetic fixtures must be authored for Ngabo and clearly labelled synthetic;
- compatibility field names/mappings should be documented factually and minimally;
- if any official sample file/schema is copied rather than independently represented, record its source and usage permission here before merge.

The safe default is **format compatibility + Ngabo-authored synthetic fixtures**, not redistribution of third-party datasets.

---

## 5. Approved AMR Guidance Corpus Register

Every source placed in the curated evidence corpus must have an entry with at least:

```text
source_id
publisher
canonical_title
canonical_url
publication/version date
content stored locally (yes/no)
stored material type (metadata / excerpt / full text)
license / permission / usage basis
required attribution
retrieval eligibility
notes
```

### Evidence-content policy

Prefer this order:

1. metadata + official URL + locally authored indexing summary where sufficient;
2. short permitted excerpts with provenance where appropriate;
3. openly licensed/public-domain content when the license permits the intended storage/redistribution;
4. full-text storage only when rights/terms clearly permit it.

Do not copy an entire third-party guideline into the public repository merely because it is publicly readable online.

EmbeddingGemma indexing does not change copyright/licensing obligations. Only approved, provenance-recorded material may enter the retrieval corpus.

---

## 6. Evidence Manifest Template

Add one row per evidence source during corpus construction.

| Source ID | Publisher | Title | URL | Version/date | Local content | Usage basis/license | Attribution required | Approved for retrieval |
|---|---|---|---|---|---|---|---|---|
| `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | metadata/excerpt/full | `TBD` | `TBD` | no until verified |

No source is considered approved merely because it appears in this table. `Approved for retrieval` must be explicitly changed to `yes` after verification.

---

## 7. Pre-Existing Work Disclosure Register

The hackathon allows standard frameworks, libraries, starter templates, and AI coding assistants, but requires disclosure of other pre-existing code/work incorporated into the project.

### Default rule

Do not import pre-existing application code into Ngabo silently.

If any pre-existing code, dataset, template beyond ordinary framework scaffolding, model artifact, design asset, or prior project component is reused, record:

```text
item
original creation/source date
original repository/source
owner
what was reused
what was newly built during the submission period
license/authorization
where disclosed in Devpost submission
```

### Register

| Item | Pre-existing? | Reuse approved? | Disclosure required? | Notes |
|---|---|---|---|---|
| Ngabo application/domain implementation | No pre-existing implementation should be imported without a new entry | N/A | If imported later, yes | Build submitted implementation during contest period |
| Standard framework/library code | Standard development dependency | Yes subject to license | Normally covered through dependency inventory | Do not claim dependency code as original Ngabo work |
| AI coding assistant output | Development assistance | Permitted by contest rules subject to entrant ownership/compliance | Describe tooling if useful/required | Entrant remains responsible for submitted code |
| Prior personal/project code | Unknown until proposed | **No by default** | Yes if incorporated | Review before merge |

Do not represent this initial register as a factual declaration that no pre-existing material will ever be used. It is a control requiring disclosure if reuse occurs.

---

## 8. Third-Party Logos / Screenshots / Demo Media

Submission/demo assets must also respect third-party rights.

Rules:

- do not imply sponsorship/endorsement by WHO, Google, hospitals, universities, government bodies, or other organizations;
- use official product/service names factually where needed for architecture/technology explanation;
- avoid unnecessary third-party logos in submission media unless permitted;
- screenshots of Google Cloud used as deployment proof should focus on Ngabo resources and avoid exposing account identifiers/secrets;
- demo emails/webhooks must use authorized test targets;
- stock/media assets require a documented usable license if included.

---

## 9. Dependency Inventory at Submission Freeze

Before the release candidate is frozen:

- [ ] lockfiles are committed;
- [ ] exact direct dependency versions are known;
- [ ] licenses/notices for shipped open-source dependencies are reviewed/generated where appropriate;
- [ ] no secrets/API keys are in source/history;
- [ ] evidence-corpus sources are provenance-complete;
- [ ] optional model licenses/terms have been verified for the exact integration;
- [ ] any pre-existing work is disclosed;
- [ ] any third-party data used in demo/evaluation is authorized;
- [ ] no real patient/lab data is included;
- [ ] public claims do not imply unauthorized endorsement.

---

## 10. Submission Disclosure Requirements

The Devpost project description should truthfully list:

- Google/third-party technologies actually used;
- data sources actually used;
- whether the public dataset is synthetic;
- any pre-existing non-standard work incorporated;
- any optional model only if actually integrated;
- known limitations relevant to judging/reproducibility.

Cross-check this register against `docs/SUBMISSION_EVIDENCE.md` before submission.

---

## 11. Stop Conditions

Stop integration/release if:

- the license/terms for a dataset/model/dependency cannot be established;
- a copied source cannot be redistributed under the intended repository/submission model;
- pre-existing code ownership is unclear;
- a demo asset could imply unauthorized sponsorship;
- evidence corpus provenance is incomplete;
- a model bonus would require claiming an integration that is not actually functioning.
