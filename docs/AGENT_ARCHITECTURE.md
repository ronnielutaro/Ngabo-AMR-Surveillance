# Ngabo — Agent & Workflow Design

**Version:** 0.4  
**Date:** 2026-08-16  
**Framework:** Google ADK (Python)  
**Primary model:** Gemini 3.6 Flash

---

## 1. Principle

Ngabo is not “a bunch of agents talking to each other.”

The v0.1 runtime is one bounded Gemini reasoning role embedded inside an explicit deterministic workflow.

The hero workflow completes without human intervention, but Gemini does not own scientific truth, action authorization, freshness or idempotency.

---

## 2. Agent Role

Gemini is responsible for:

- reasoning across joined deterministic findings;
- selecting bounded approved-evidence intent when ambiguous;
- forming labelled hypotheses;
- synthesizing approved evidence into a structured incident package;
- repairing a package from structured deterministic validator feedback;
- stopping with uncertainty when evidence is insufficient.

Gemini is **not** responsible for:

- signal calculation;
- profile/baseline math;
- schema validation;
- fixed routing;
- action class assignment;
- allow-list authorization;
- freshness/material-change detection;
- idempotency;
- external action side effects;
- acknowledgement state transitions;
- prescribing/diagnosis/outbreak confirmation.

---

## 3. Canonical Hero Runtime

```text
signal event
  ↓
context function
  ↓
parallel deterministic branches
  ├─ profile comparison
  ├─ baseline summary
  └─ missingness assessment
  ↓
join
  ↓
Gemini triage
  ↓
approved evidence retrieval
  ↓
Gemini synthesis
  ↓
deterministic validator
  ├─ valid → continue
  └─ invalid → bounded Gemini repair → validator
  ↓
deterministic autonomy policy
  ├─ A1 → continue
  └─ blocked/insufficient → abstain
  ↓
freshness
  ↓
idempotency
  ↓
external A1 action adapter
  ↓
machine acknowledgement
```

No human clarification/approval node is required in the hero path.

---

## 4. Hero No-Question Rule

The hero fixture must be complete enough for safe A1 coordination.

If a non-hero incident lacks a material fact:

```text
material missingness
→ NEEDS_INFORMATION
→ autonomous abstention
```

The model must not fabricate the value and should not route to a human merely to preserve “completion.”

---

## 5. Structured Inputs

Gemini should receive a bounded structured investigation context such as:

```json
{
  "incident_id": "INC-001",
  "signal": {},
  "profile_comparison": {},
  "baseline_summary": {},
  "missing_fields": [],
  "approved_evidence": [],
  "known_uncertainties": []
}
```

Canonical facts are loaded from application state, not remembered from prior model conversation.

---

## 6. Structured Output

Final synthesis uses a strict schema similar to:

```json
{
  "title": "...",
  "priority": "HIGH",
  "observed_evidence": [],
  "derived_findings": [],
  "hypotheses": [],
  "uncertainties": [],
  "missing_information": [],
  "guidance": [],
  "investigation_checklist": [],
  "draft_coordination_message": "...",
  "limitations": []
}
```

The output is a draft machine artifact until deterministic validation succeeds.

---

## 7. Deterministic Validation / Repair

Validator checks include:

- isolate/source IDs exist;
- observed/derived claims map to canonical/deterministic inputs;
- guidance is source-backed;
- prohibited diagnosis/prescribing/outbreak-confirmation language absent;
- required fields present;
- coordination message is compatible with A1-safe wording.

Repair loop:

```text
validation errors
→ Gemini repair
→ validation
```

Hard max attempts, suggested `2`.

No model override of validator.

---

## 8. Evidence Capability

Evidence retrieval is behind `EvidenceSearchPort`.

Core may use deterministic/tag retrieval.

After core:

- EmbeddingGemma may provide semantic retrieval over approved corpus;
- MedGemma may be a bounded evidence-interpretation capability only if evaluation proves benefit.

No arbitrary external web browsing becomes approved guidance.

---

## 9. Action Policy Is Not an Agent Tool

The model may draft a safe coordination message, but final execution eligibility is determined by deterministic policy.

```text
package
→ ActionPolicy
→ A0/A1/A2/A3
```

A1 may execute automatically after all gates.

A2/A3 cannot be upgraded by model text.

The agent has no unrestricted `send_alert` tool.

---

## 10. External Action Boundary

```text
application workflow
→ NotificationPort
→ authorized A1 adapter
→ external target
```

The model does not call the provider directly.

The external target returns a machine acknowledgement event/callback that is handled through an application use case.

---

## 11. Context / Memory

Before every agent run/recovery, build current context from canonical state.

ADK session/checkpoint is execution continuity, not truth.

Long-term model memory is not used as factual AMR evidence in v0.1.

---

## 12. Failure Handling

Agent/runtime must handle:

- Gemini failure/timeout;
- evidence unavailable;
- invalid package;
- repair exhaustion;
- required deterministic branch failure;
- stale context;
- external action failure;
- duplicate events.

Failure must be explicit and may cause autonomous abstention.

---

## 13. Model / Tool Budgets

Configure explicit limits for:

- model calls;
- repair attempts;
- tool/capability calls;
- total execution time;
- retries.

No unbounded loops.

Track canonical hero call counts in evaluation.

---

## 14. Collaborative Agents

Not required for core v0.1.

Potential future specialists are only justified if evaluation shows measurable benefit.

Prefer deterministic functions or bounded stateless model capabilities before creating another autonomous agent.

---

## 15. Dynamic Workflow

Deferred.

The hero incident workflow is known in advance and should remain explicit.

---

## 16. ADK Implementation Risk

Exact runtime primitives must be proven via `docs/ADK_CAPABILITY_SPIKE.md`.

If first-class workshop graph APIs differ from pinned ADK Python:

- preserve semantic graph using supported workflow agents/application orchestration;
- do not invent APIs;
- do not add another framework merely to recreate the workshop syntax.

---

## 17. Observability

Log observable facts:

- graph/node/branch/join execution;
- model name/call status;
- evidence retrieval;
- package validation/repair;
- action class/policy decision;
- freshness;
- idempotency;
- external delivery;
- machine acknowledgement;
- retry/abstention.

No chain-of-thought.

---

## 18. Evaluation

Hero trajectory should prove:

```text
0 human prompts
0 human interventions
0 clarification
0 approval
required deterministic branches executed
bounded Gemini stages executed
package valid
A1 policy authorized
freshness/idempotency passed
1 external effect
1 machine acknowledgement
```

Non-hero safety evals prove material missingness/A2/A3/invalid packages abstain.

---

## 19. Definition of Done

- [ ] Gemini reasoning is bounded to ambiguous tasks;
- [ ] deterministic stages own science/policy;
- [ ] hero has no human interaction;
- [ ] invalid package auto-repairs or stops;
- [ ] A2/A3 cannot auto-execute;
- [ ] external action is outside model tool access;
- [ ] machine acknowledgement closes loop;
- [ ] context rebuild/freshness/idempotency protect action;
- [ ] ADK APIs are pinned/proven;
- [ ] evals prove trajectory and safety.
