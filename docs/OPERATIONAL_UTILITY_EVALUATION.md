# Ngabo — Operational Utility Evaluation

**Status:** Required v0.1 hackathon evaluation contract  
**Date:** 2026-08-16  
**Primary judging criterion:** Innovation & Operational Utility (40%)

---

## 1. Purpose

Ngabo must prove more than technical correctness. The hackathon's highest-weighted criterion asks whether the system removes real-world friction through high-value autonomous execution rather than simple chat.

This document defines how Ngabo will measure that claim without inventing hospital productivity numbers or presenting a synthetic benchmark as clinical validation.

The core question is:

> **How much human coordination and manual assembly does Ngabo remove between a surveillance signal and a review-ready incident package / approved response action?**

---

## 2. Reference Workflow

The evaluation compares two flows over the same synthetic incident scenario.

### Reference manual workflow

A scripted reference workflow represents the coordination work a user would otherwise need to perform:

```text
review surveillance signal
→ inspect affected isolates
→ compare resistance profiles
→ inspect baseline/context
→ identify missing fields
→ locate approved guidance
→ assemble findings
→ draft an incident brief
→ route for review
→ prepare/send an approved action
→ track acknowledgement
```

This is a **reference workflow for software evaluation**, not a claim that every hospital follows these exact steps.

### Ngabo workflow

```text
surveillance signal
→ Pub/Sub event
→ ADK graph starts automatically
→ deterministic fan-out/join
→ bounded Gemini triage
→ approved evidence retrieval
→ one targeted clarification only if materially necessary
→ evidence-grounded synthesis
→ deterministic package validation
→ human review
→ deterministic freshness barrier
→ authorized external action
→ acknowledgement
```

---

## 3. Required Operational Metrics

Record these metrics for the canonical seeded scenario.

| Metric | Definition | Why it matters |
|---|---|---|
| `signal_to_review_ready_ms` | Time from persisted surveillance signal to validated package entering `WAITING_FOR_REVIEW` | Measures coordination latency |
| `human_intervention_count` | Number of times a human must provide information or make a decision before action | Measures autonomy |
| `human_active_steps` | Count of explicit user actions required by the scripted workflow | Measures workflow friction |
| `clarification_count` | Number of targeted clarification questions | Penalizes unnecessary interruptions |
| `manual_prompt_count_to_start` | User prompts required to start investigation | Must be zero for Taskmaster flow |
| `evidence_searches_completed_by_system` | Approved-corpus retrieval operations performed without manual lookup | Shows autonomous evidence work |
| `signal_to_action_ready_ms` | Time from signal to a fresh approved action becoming executable | Measures end-to-end readiness |
| `action_to_ack_ms` | Time from external action attempt to acknowledgement/completion signal | Measures closed-loop response |
| `resume_count` | Number of safe workflow resumes/recoveries | Demonstrates long-running operation where exercised |
| `model_call_count` | Gemini calls in canonical flow | Engineering/cost discipline, not medical quality |
| `deterministic_node_count` | Required deterministic graph nodes executed | Shows heavy lifting is not delegated blindly to the model |

Do not label any of these as clinical outcome metrics.

---

## 4. Human-Touch Accounting

A human interaction counts when a user must actively provide information, make a decision, or manually perform coordination that could otherwise block the workflow.

### Expected canonical Ngabo human boundaries

The canonical demo should require only:

1. one targeted clarification if the seeded scenario intentionally omits a material field; and
2. final consequential review/approval.

Importing or triggering the synthetic demo scenario is a demo setup action and should be reported separately from incident-response human touches.

The human does **not**:

- prompt Ngabo to begin the investigation;
- choose which deterministic calculations to run;
- manually sequence profile/baseline/missingness analysis;
- manually construct the evidence package;
- tell the agent which fixed routing branch to take;
- manually send the external action after approving it.

This distinction is central to the Taskmaster narrative.

---

## 5. Before-vs-After Protocol

For the canonical synthetic incident:

1. Freeze the dataset, expected signal, approved evidence corpus, and target action adapter.
2. Define the manual reference script in `EVALUATION.md`.
3. Run the reference workflow with the same available information.
4. Record human steps and elapsed time without optimizing the manual script after seeing Ngabo's result.
5. Run the deployed Ngabo workflow at least three times.
6. Record the operational metrics above for each run.
7. Report median and range for timing metrics; report exact counts for human/model/tool/node actions.
8. Explain any failure/retry rather than deleting inconvenient runs.

If a meaningful manual-time comparison cannot be executed credibly before submission, report **step/handoff reduction only** and do not manufacture a time-saved percentage.

---

## 6. Minimum Taskmaster Evidence

The submission/demo should make these facts directly observable:

- investigation starts from the surveillance event, not a chat prompt;
- independent investigation work executes automatically;
- Gemini is used only where ambiguity/reasoning adds value;
- a clarification interrupts the workflow only when needed;
- the same incident resumes after the answer;
- the system produces a review-ready structured package;
- the professional review is a safety boundary, not workflow micromanagement;
- after approval, Ngabo performs the authorized external action automatically if freshness validation passes;
- acknowledgement closes the workflow.

---

## 7. Operational Utility Claims Policy

Allowed after measurement:

- “In our committed synthetic benchmark, Ngabo reduced the scripted workflow from X human active steps to Y.”
- “The deployed canonical scenario reached a review-ready package in a median of X seconds across N runs.”
- “The investigation started with zero user prompts.”

Not allowed without real evidence:

- “Ngabo saves hospitals 80% of surveillance time.”
- “Ngabo reduces outbreak response time by X% in Uganda.”
- “Ngabo improves patient outcomes.”
- “Ngabo is clinically validated.”

Keep software-benchmark claims separate from clinical/public-health claims.

---

## 8. Failure and Friction Metrics

Also record:

- unnecessary clarification rate in committed scenarios;
- visible failure count;
- retries;
- duplicate-event suppressions;
- stale-approval blocks;
- notification retry behavior;
- no-evidence cases that correctly stop/degrade rather than hallucinate.

A system that completes fast by hiding failures does not score well on operational utility.

---

## 9. `EVALUATION.md` Requirements

The public submission evaluation must contain an **Operational Utility** section with:

- reference workflow definition;
- scenario description;
- human-step accounting method;
- raw/summary timing results;
- Ngabo human-intervention count;
- zero-prompt autonomous-start evidence;
- model/function/tool trajectory counts;
- limitations of the benchmark;
- explicit statement that results use synthetic data and are not clinical validation.

---

## 10. Demo Integration

The four-minute demo does not need to show a stopwatch comparison live.

Prefer:

1. demonstrate the autonomous workflow;
2. briefly show the measured operational-utility result card/table;
3. link the public `EVALUATION.md` for methodology and full results.

Do not consume demo time narrating every internal metric.

---

## 11. Acceptance Criteria

- [ ] canonical reference workflow is documented;
- [ ] human active steps are defined consistently;
- [ ] `manual_prompt_count_to_start == 0` for the Taskmaster path;
- [ ] canonical Ngabo human boundaries are clarification-if-needed + final review;
- [ ] deployed runs capture signal-to-review-ready latency;
- [ ] operational metrics are generated from real executions, not documentation estimates;
- [ ] no synthetic benchmark is presented as hospital/clinical validation;
- [ ] `EVALUATION.md` contains before-vs-after operational utility evidence before submission.
