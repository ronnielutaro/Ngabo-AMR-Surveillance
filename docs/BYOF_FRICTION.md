# Ngabo — Bring Your Own Friction (BYOF) Narrative & Validation Contract

**Status:** Required v0.1 hackathon narrative/evaluation contract  
**Date:** 2026-08-16  
**Primary judging criterion:** Innovation & Operational Utility (40%)

---

## 1. Purpose

The Taskmaster judging rubric explicitly asks whether the project uses the **Bring Your Own Friction (BYOF)** mandate to solve a unique, personal problem.

Ngabo must therefore tell a truthful first-person friction story rather than relying only on the abstract importance of antimicrobial resistance.

This document defines the story we can support without pretending the builder is a hospital microbiologist or claiming unvalidated hospital workflow facts.

---

## 2. The Personal Friction

The personal friction is the repeated manual coordination work involved in turning AMR surveillance data into a defensible, evidence-backed investigation package while building and researching Ngabo.

The builder's recurring workflow is:

```text
inspect a surveillance signal / synthetic microbiology export
        ↓
identify which isolates are implicated
        ↓
compare resistance patterns
        ↓
inspect temporal/location/baseline context
        ↓
check missing information
        ↓
search trusted AMR guidance
        ↓
separate observed facts from hypotheses
        ↓
assemble a structured incident brief
        ↓
validate claims and source references
        ↓
route the resulting information/action
        ↓
track whether the workflow completed
```

This is a real software/research-builder friction: the work is fragmented across data inspection, calculations, evidence lookup, reasoning, writing, validation and coordination.

Ngabo automates that workflow.

---

## 3. What We Must Not Claim

Do not say:

- the builder personally performs official hospital AMR surveillance unless that becomes true and is documented;
- every Ugandan hospital follows the exact reference workflow;
- Ngabo has already been validated by clinicians unless validation actually occurs;
- the personal-friction story proves clinical effectiveness;
- a synthetic benchmark proves national public-health impact.

The BYOF story is about the builder's **own repeated coordination/research workflow**, not borrowed identity.

---

## 4. Submission-Friendly Narrative

A concise truthful version:

> While researching antimicrobial resistance and building Ngabo, I kept running into the same messy workflow: a surveillance signal was only the beginning. I still had to inspect the isolates, compare resistance patterns, check context, find trusted guidance, separate facts from hypotheses, assemble a defensible incident brief, validate the sources, and route the result. Ngabo is the agent I wanted for that friction: it watches for a signal and completes that surveillance-to-investigation coordination workflow automatically.

This can be tightened for Devpost/video, but its meaning must remain truthful.

---

## 5. Why This Is a Strong Taskmaster Friction

The friction is:

- **multi-step** rather than a single prompt;
- **event-driven** because work begins when surveillance data changes;
- **cross-capability** because it combines calculations, retrieval, reasoning, validation, persistence and external action;
- **repeatable** because every new signal recreates the coordination burden;
- **high-value** because the output is a structured investigation package rather than generic text;
- **personally grounded** because it comes from the builder's own AMR research/build workflow.

---

## 6. Operational Utility Benchmark Link

`docs/OPERATIONAL_UTILITY_EVALUATION.md` must use this builder reference workflow as the primary BYOF benchmark.

The evaluation should measure at least:

```text
reference_human_active_steps
ngabo_human_active_steps
manual_prompt_count_to_start
human_intervention_count
signal_to_review_ready_ms
signal_to_autonomous_action_ms
action_to_ack_ms
model_call_count
deterministic_node_count
```

For the canonical Taskmaster hero path:

```text
ngabo_human_active_steps == 0
human_intervention_count == 0
manual_prompt_count_to_start == 0
clarification_count == 0
```

---

## 7. Optional Practitioner Validation — Strengthening, Not Fabrication

Practitioner feedback can strengthen product relevance, but it is separate from the BYOF claim.

If time permits, conduct short workflow-validation conversations with relevant people such as:

- clinical/diagnostic microbiology professionals;
- AMR surveillance officers;
- infection prevention/control professionals;
- antimicrobial stewardship professionals;
- public-health informatics/AMR researchers.

Ask about workflow, not endorsements:

1. What happens after a suspicious resistance pattern is noticed?
2. Which steps are most manual?
3. What information must be assembled before someone can act?
4. Where do handoffs or delays occur?
5. Which actions could safely be automated?
6. Which decisions must remain professionally governed?
7. What would make an autonomous investigation package useful or dangerous?

Do not publish names/quotes without permission.

---

## 8. Practitioner Evidence Policy

If feedback is obtained, record only what is supportable:

```text
interview date
role category
workflow observations
product implications
permission status for attribution/quotation
```

Allowed:

> “We tested the workflow assumptions with two AMR/microbiology practitioners and used their feedback to refine the incident package.”

Only if true.

Not allowed:

> “Ugandan hospitals validated Ngabo.”

unless a formal validation actually happened.

---

## 9. Demo Friction Story

The first 20–30 seconds of the video should make the friction concrete.

Suggested structure:

1. Show the synthetic AMR data / signal.
2. Explain that the signal is not the finished work.
3. Flash the manual friction sequence: compare → contextualize → find evidence → assemble → validate → route → track.
4. State: **“I kept doing this manually while building and researching AMR workflows, so I built Ngabo to complete it in the background.”**
5. Trigger the autonomous workflow.

Avoid spending the opening on broad AMR statistics before the judge understands the personal friction.

---

## 10. Evidence to Preserve

Before submission preserve:

- the committed reference workflow;
- raw benchmark runs;
- measured human-step counts;
- screenshots/video showing the autonomous replacement workflow;
- optional practitioner-validation notes where consent permits;
- the exact Devpost/video BYOF wording used.

---

## 11. Acceptance Criteria

The BYOF gap is closed when:

- [ ] Devpost/video clearly state the builder's personal friction;
- [ ] the friction is a concrete repeated workflow, not “AMR is a big problem”;
- [ ] the reference workflow is measured in `EVALUATION.md`;
- [ ] hero Ngabo path requires zero human intervention;
- [ ] no borrowed clinical identity is implied;
- [ ] optional practitioner feedback is reported only if actually obtained;
- [ ] the value proposition directly connects the personal friction to the autonomous workflow.
