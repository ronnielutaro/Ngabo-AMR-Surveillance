# ADR 0007 — Zero-Human Safe Coordination for the Taskmaster Hero

**Status:** Accepted  
**Date:** 2026-08-16

## Context

The All Things Agentic Hackathon's Taskmaster judging rubric explicitly asks whether the agent intercepts and completes a multi-step background workflow **without human intervention**.

Earlier Ngabo v0.1 designs placed targeted clarification and human approval inside the canonical demo workflow. That was safety-conscious, but it weakened the literal Taskmaster interpretation and made the highest-weighted Innovation & Operational Utility story less decisive.

Removing all safety boundaries would be unacceptable because Ngabo operates in an AMR/health context.

We therefore need a design that satisfies both:

1. literal zero-human Taskmaster completion; and
2. strong constraints against autonomous clinical/official public-health decisions.

## Decision

Adopt a **dual-lane action architecture**.

### Autonomous hero lane

The canonical v0.1 Taskmaster workflow completes from surveillance event to machine acknowledgement with:

```text
0 prompts
0 human interventions
0 clarifications
0 approval clicks
```

The hero may autonomously execute only **A1 safe external coordination** actions after deterministic validation, policy, freshness and idempotency gates.

### Action classes

```text
A0 INTERNAL_STATE
A1 SAFE_EXTERNAL_COORDINATION
A2 REAL_OPERATIONAL_ESCALATION
A3 CLINICAL_OR_OFFICIAL_PUBLIC_HEALTH_DECISION
```

A0/A1 may be autonomous under policy.

A2 is outside the public-v0.1 automatic envelope by default.

A3 is forbidden as autonomous v0.1 action.

Gemini does not own this classification.

### Missing data

The hero fixture must contain all material data required for A1 completion.

Other incidents with material missing information autonomously abstain instead of requiring a human clarification merely to complete the workflow.

### Model errors

Use deterministic package validation and a bounded automatic repair loop. Exhausted repair budget stops safely.

### External completion

Hero action uses a real authorized external test/sandbox/internal integration with machine acknowledgement so no person must acknowledge completion.

## Consequences

### Positive

- directly satisfies literal Taskmaster zero-human criterion;
- strengthens BYOF/operational utility score narrative;
- keeps demo simpler and more legible;
- demonstrates sophisticated policy engineering rather than removing safety;
- creates measurable `human_intervention_count == 0` target;
- machine acknowledgement proves true closed-loop automation;
- safety failures become deterministic abstention instead of ad hoc human rescue.

### Tradeoffs

- requires explicit action policy and allow-listing;
- requires complete hero fixture;
- requires automatic package repair;
- requires external service capable of automated acknowledgement;
- demo hero no longer showcases human pause/resume, which moves to evaluation/secondary proof;
- A1 must be carefully worded so judges see real action without interpreting it as clinical authority.

## Superseded v0.1 Wording

This ADR supersedes older v0.1 requirements that made **human approval or clarification mandatory in the canonical hackathon hero workflow**.

Those patterns remain valid for:

- future A2/A3 real-world workflows;
- shadow/pilot deployments;
- secondary long-running-agent evaluations;
- optional multimodal verification.

They are not required for the A1 Taskmaster hero.

## Safety Invariants Preserved

Ngabo still may not autonomously:

- diagnose;
- prescribe;
- confirm/declare outbreak;
- fabricate missing clinical facts;
- act on invalid package/evidence;
- send to unauthorized target;
- act on stale state;
- duplicate side effects on retry.

## Evaluation

ADR is implemented only when deployed evidence proves:

```text
manual_prompt_count_to_start == 0
human_intervention_count == 0
clarification_count == 0
approval_click_count == 0
external_effect_count == 1
machine_acknowledgement_count == 1
```

and safety evals prove A2/A3 are blocked.

## References

- `docs/HACKATHON_ALIGNMENT.md`
- `docs/TASKMASTER_ZERO_HUMAN_AUTONOMY.md`
- `docs/BYOF_FRICTION.md`
- `docs/DATA_SAFETY_EVALUATION.md`
- `docs/OPERATIONAL_UTILITY_EVALUATION.md`
