# Ngabo — Google ADK Capability Spike

**Status:** Required before implementing the v0.1 agent runtime  
**Date:** 2026-08-16

---

## 1. Purpose

Ngabo's architecture is intentionally graph-first, resumable and observable. Workshop terminology and rapidly evolving ADK APIs must not be treated as stable implementation names without verification.

Before writing the production ADK orchestration layer, perform a small executable capability spike against the **exact pinned Google ADK Python version** that the repository will ship.

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
8. a short result section in this document or an ADR amendment.

Do not merge graph runtime implementation until this spike is green.

---

## 3. Capabilities to Verify

Verify current, documented APIs for:

### Core agent/tool runtime

- LLM agent construction;
- ordinary function tools;
- structured outputs;
- invocation/session identifiers;
- callbacks/lifecycle hooks;
- configured model/tool/time/loop bounds where supported.

### Deterministic orchestration

Determine the supported implementation for:

- sequential execution;
- parallel execution;
- join/synchronization;
- fixed deterministic routing;
- deterministic Python/function work inside the workflow;
- passing typed outputs between stages.

If the exact first-class `function node` / `join node` workshop API is unavailable, preserve the architecture using supported ADK workflow agents and ordinary Python/application orchestration rather than inventing unsupported APIs.

### Resumability / long-running execution

Verify:

- resumability configuration/API;
- human-input or pause/resume primitives if relevant to non-hero evaluation paths;
- long-running function/tool primitives;
- session persistence requirements;
- what survives process restart;
- what must remain in Firestore/application state.

### Evaluation / observability

Verify:

- eval dataset format;
- trajectory/tool evaluation support;
- trace identifiers;
- Cloud Trace/OpenTelemetry path;
- safe content-capture controls;
- Agents CLI compatibility if used.

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

If ADK requires a different outer composition shape, change the infrastructure implementation—not the domain/application contract merely to fit the vendor.

---

## 5. Graph Fallback Ladder

Use the simplest supported mechanism that preserves semantics.

### Preferred

First-class supported ADK graph/workflow primitives that can express:

```text
context
→ parallel deterministic work
→ join
→ Gemini triage
→ evidence
→ Gemini synthesis
→ deterministic validation
```

### Fallback A

Supported `SequentialAgent` / `ParallelAgent` / related workflow agents plus thin custom deterministic adapters.

### Fallback B

Application-owned deterministic workflow state machine invokes bounded ADK agent nodes at the two model-reasoning boundaries.

Fallback B is acceptable because the business workflow is already application-owned; ADK still provides the actual Gemini agent runtime, tool/capability integration, sessions/evals/observability.

Do **not**:

- invent undocumented ADK class names;
- block the hackathon waiting for a preview API;
- move scientific/business logic into prompts to fit a framework abstraction;
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
Gemini structured decision
  ↓
deterministic validator
  ↓
structured result
```

Then repeat one run with a controlled failure in a required parallel branch and prove downstream synthesis does not falsely report success.

---

## 7. Zero-Human Hero Compatibility

The selected ADK path must support Ngabo's canonical autonomous hero flow without requiring an interactive prompt once the event handler starts the workflow.

The runtime API must allow the application to invoke/run the agent workflow from a Pub/Sub-triggered process or equivalent backend event path.

`adk web` / developer playground interaction is not evidence of Taskmaster autonomy.

---

## 8. Version Pinning

Once the spike passes:

- pin the exact runtime dependency in `uv.lock`;
- record the version in README/EVALUATION/deployment evidence;
- do not upgrade during demo freeze unless fixing a blocking defect;
- rerun graph/resume/eval tests after any ADK version change.

---

## 9. Acceptance Criteria

- [ ] exact ADK Python version recorded;
- [ ] exact supported orchestration primitives recorded;
- [ ] parallel deterministic execution proven;
- [ ] join/failure semantics proven;
- [ ] structured Gemini output proven;
- [ ] validator boundary proven;
- [ ] backend/event invocation proven without interactive chat;
- [ ] resume API/fallback decision recorded;
- [ ] eval/observability path recorded;
- [ ] framework fallback selected if workshop terminology differs;
- [ ] no unsupported API assumptions remain in implementation plan.
