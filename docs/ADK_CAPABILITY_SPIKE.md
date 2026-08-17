# Ngabo — Google ADK Capability Spike

**Status:** Required before implementing the v0.1 agent runtime  
**Date:** 2026-08-17

---

## 1. Purpose

Ngabo's architecture is graph-first, resumable, observable, and now requires **Proof-Carrying Autonomy**. Workshop terminology and rapidly evolving ADK APIs must not be treated as stable implementation names without verification.

Before writing production ADK orchestration, perform a small executable capability spike against the **exact pinned Google ADK Python version** that the repository will ship.

The goal is to remove framework/API uncertainty before it can threaten the hackathon critical path.

---

## 2. Required Outputs

The spike must produce:

1. exact Python version;
2. exact `google-adk` version;
3. exact Gemini model configuration;
4. a tiny runnable orchestration example;
5. a mapping from Ngabo architecture concepts to supported ADK primitives;
6. explicit fallback choices for any workshop primitive not available/stable;
7. tests proving the selected implementation path works;
8. proof that Gemini structured output can be parsed into Ngabo's proof-carrying DTO/schema;
9. proof that deterministic claim verification remains outside Gemini/ADK authority;
10. a short result section in this document or an ADR amendment.

Do not merge graph runtime implementation until this spike is green.

---

## 3. Capabilities to Verify

### Core agent/tool runtime

- LLM agent construction;
- ordinary function tools;
- structured outputs / schema-constrained output path;
- invocation/session identifiers;
- callbacks/lifecycle hooks;
- configured model/tool/time/loop bounds where supported.

### Proof-Carrying Autonomy compatibility

Verify the chosen ADK/Gemini path can return a typed object equivalent to:

```text
claim_id
claim_type
statement
supporting_record_ids[]
supporting_finding_ids[]
supporting_source_ids[]
contradicting_claim_ids[]
uncertainties[]
requested_action_class
confidence_label
```

The spike must demonstrate:

- valid structured output parses successfully;
- malformed output is caught before action;
- model output can be passed to ordinary deterministic Python/application verification;
- verifier result—not model self-assessment—controls downstream route;
- verifier can return stable structured error codes to a bounded repair call;
- private chain-of-thought is neither required nor persisted as proof.

### Deterministic orchestration

Determine supported implementation for:

- sequential execution;
- parallel execution;
- join/synchronization;
- fixed deterministic routing;
- deterministic Python/function work inside workflow;
- passing typed outputs between stages;
- routing verifier failure to bounded repair or abstention.

If exact first-class `function node` / `join node` workshop API is unavailable, preserve architecture using supported ADK workflow agents and ordinary Python/application orchestration rather than inventing unsupported APIs.

### Resumability / long-running execution

Verify:

- resumability configuration/API;
- human-input or pause/resume primitives if relevant to non-hero evaluation paths;
- long-running function/tool primitives;
- session persistence requirements;
- what survives process restart;
- what must remain in Firestore/application state;
- proof/package verification status can be rebuilt/rechecked from canonical state after restart.

### Evaluation / observability

Verify:

- eval dataset format;
- trajectory/tool evaluation support;
- trace identifiers;
- Cloud Trace/OpenTelemetry path;
- safe content-capture controls;
- Agents CLI compatibility if used;
- custom metadata/events for `CLAIM_VERIFICATION_*` and repair events where practical.

---

## 4. Architecture Preservation Rule

Framework APIs may change. Ngabo's dependency direction may not.

```text
ADK primitive
     ↓
infrastructure adapter
     ↓
application use case/query/port
     ↓
domain policy
```

Proof verification stays inside application/domain contracts and does not depend on Google SDK classes.

If ADK requires a different outer composition shape, change infrastructure implementation—not domain/application contract merely to fit vendor APIs.

---

## 5. Graph Fallback Ladder

Use simplest supported mechanism preserving semantics.

### Preferred

First-class supported ADK graph/workflow primitives expressing:

```text
context
→ parallel deterministic work
→ join
→ Gemini triage
→ approved evidence
→ Gemini proof-carrying synthesis
→ deterministic claim verifier
→ bounded repair / abstention
```

### Fallback A

Supported `SequentialAgent` / `ParallelAgent` / related workflow agents plus thin custom deterministic adapters.

### Fallback B

Application-owned deterministic workflow state machine invokes bounded ADK agent nodes at model-reasoning boundaries.

Fallback B is acceptable because business workflow and proof policy are application-owned; ADK still provides the actual Gemini agent runtime, capability integration, sessions/evals/observability.

Do **not**:

- invent undocumented ADK class names;
- block the hackathon waiting for a preview API;
- move scientific/proof/action policy into prompts to fit framework abstraction;
- add LangGraph or another orchestration framework merely because an ADK primitive is missing.

---

## 6. Minimum Spike Scenario

The spike need not use AMR data initially.

It must prove this shape:

```text
input
  ↓
deterministic context function
  ↓
parallel deterministic function A + B
  ↓
join
  ↓
Gemini structured proof-carrying decision
  ↓
deterministic verifier
  ├─ valid → structured result
  └─ invalid → structured errors → bounded repair → verifier
```

Then repeat with:

1. a controlled required-branch failure and prove downstream synthesis does not falsely report success;
2. a fabricated proof reference and prove deterministic verifier blocks continuation;
3. a deliberately malformed structured model output and prove it cannot reach action routing.

---

## 7. Zero-Human Hero Compatibility

Selected ADK path must support canonical autonomous hero without requiring an interactive prompt once event handler starts workflow.

Runtime API must allow application to invoke/run agent workflow from a Pub/Sub-triggered process or equivalent backend event path.

`adk web` / developer playground interaction is not evidence of Taskmaster autonomy.

---

## 8. Version Pinning

Once spike passes:

- pin exact runtime dependency in `uv.lock`;
- record version in README/EVALUATION/deployment evidence;
- do not upgrade during demo freeze unless fixing a blocking defect;
- rerun graph/proof/resume/eval tests after any ADK version change.

---

## 9. Acceptance Criteria

- [ ] exact ADK Python version recorded;
- [ ] exact supported orchestration primitives recorded;
- [ ] parallel deterministic execution proven;
- [ ] join/failure semantics proven;
- [ ] proof-carrying structured Gemini output proven;
- [ ] deterministic claim-verifier boundary proven;
- [ ] fabricated reference blocks downstream continuation;
- [ ] bounded repair route proven;
- [ ] backend/event invocation proven without interactive chat;
- [ ] resume API/fallback decision recorded;
- [ ] eval/observability path recorded;
- [ ] framework fallback selected if workshop terminology differs;
- [ ] no unsupported API assumptions remain in implementation plan.
