# Ngabo — Hackathon Submission Freeze & Judging-Period Policy

**Status:** Required release/submission contract  
**Date:** 2026-08-16  
**Submission deadline:** 2026-08-31 17:00 PT  
**Judging period:** 2026-09-01 through 2026-10-01 per official rules

---

## 1. Purpose

The submitted project, evidence and hosted build must remain stable and judge-accessible during the judging period. Ngabo therefore treats the hackathon submission as an immutable release artifact rather than a moving development environment.

---

## 2. Freeze Principle

> **The thing judges see must be the thing we tested, documented and filmed.**

At submission freeze, record one exact release identity:

```text
Git commit SHA
release tag
Cloud Run ngabo-core revision
Cloud Run ngabo-web revision
hosted URL(s)
model/framework versions
synthetic dataset version/hash
evidence-corpus version/hash
EVALUATION.md commit
architecture diagram version
demo video URL
Devpost submission text snapshot
```

---

## 3. Git Freeze

Preferred release flow:

```text
develop
   ↓
release/v0.1.0
   ↓
main
   ↓
tag v0.1.0
```

During judging:

- `main` remains at the submitted release unless a contest administrator explicitly permits a necessary correction;
- `v0.1.0` is immutable;
- do not rewrite/tag-move submitted history;
- future development may continue on `develop`/feature branches only if it cannot alter the judged deployment or submitted evidence;
- README on the submitted release must continue to match the judged build.

If ongoing public repository work could confuse judges, prioritize a stable `main` default branch and clearly identify the submitted `v0.1.0` tag/commit in Devpost.

---

## 4. Deployment Freeze

Record exact Cloud Run revisions for:

```text
ngabo-web
ngabo-core
```

During judging:

- do not route the submitted production URLs to experimental revisions;
- do not delete Firestore/GCS/PubSub resources required for judging;
- do not rotate credentials in a way that breaks judge access;
- do not disable the external demo action/ack integration required by the submission;
- preserve seeded reset/demo behavior;
- keep costs bounded using min=0/max caps/budgets rather than shutting the project off.

Security fixes that become genuinely necessary should be handled cautiously and documented; contest rules/administrator instructions govern any substantive post-deadline change.

---

## 5. Evidence Freeze

The following become immutable submission evidence:

- public demo video;
- architecture diagram submitted/linked;
- `EVALUATION.md` results;
- operational-utility benchmark;
- screenshots used in submission;
- public article/social URLs claimed for bonus;
- final claim ledger;
- provenance/disclosure register;
- hosted build identity.

Do not edit evidence after submission in a way that makes it describe a different system than the one judged.

---

## 6. Demo Video Freeze

Before submission:

- upload the final <=4 minute video publicly to YouTube/Vimeo;
- verify playback while logged out/incognito;
- verify English audio/subtitles;
- verify Google Cloud proof is legible;
- verify the unedited autonomous execution segment is visible;
- record the video URL and publish time.

After submission, do not replace the video with a materially different build/demo.

---

## 7. Judge Access Smoke Test

Immediately before submission and periodically during judging, run a low-impact availability smoke test:

- hosted URL resolves;
- no login/credential blocker unless instructions explicitly provide credentials;
- seed/reset path works;
- core API responds;
- external test action integration remains available;
- acknowledgement path remains available;
- public repository/tag/video are accessible.

Do not run expensive full E2E scenarios continuously merely to prove availability.

---

## 8. Submission Manifest

Create a final manifest in `docs/SUBMISSION_EVIDENCE.md`:

```text
submitted_commit_sha:
submitted_tag: v0.1.0
web_revision:
core_revision:
hosted_url:
repo_url:
architecture_diagram:
evaluation_artifact:
video_url:
article_url:
social_url:
submission_timestamp:
```

Every claim in Devpost must be traceable to that manifest/release.

---

## 9. Post-Submission Development

The project may continue evolving without corrupting judging evidence if:

- work stays off submitted `main`/tag;
- judged URLs keep serving the frozen revision;
- Devpost materials remain unchanged except where contest rules/administrator explicitly permit modification;
- new work is clearly post-submission and not presented as part of the judged release.

After the judging period ends, normal release flow may resume.

---

## 10. Acceptance Criteria

- [ ] release tag/commit recorded;
- [ ] Cloud Run revisions recorded;
- [ ] deployed URLs pinned to tested revisions;
- [ ] README/evaluation/diagram/video all describe same release;
- [ ] main/tag remain stable through judging;
- [ ] judge-access smoke test passes before submission;
- [ ] external action/ack path remains usable;
- [ ] final claim ledger contains no post-freeze/unimplemented feature;
- [ ] ongoing work cannot silently alter the judged system.
