# Ngabo — Google ADK Runtime, Resumability & Evaluation Contract

**Status:** Required v0.1 agent-runtime contract  
**Version:** 0.5  
**Updated:** 2026-08-17  
**Applies to:** `services/core/ngabo/infrastructure/ai/adk` and application workflows it coordinates

---

## 1. Objective

Ngabo uses Google ADK as a real runtime capability, not a badge.

The v0.1 hero is a graph-first hybrid workflow in which:

- known scientific/policy work stays deterministic;
- independent deterministic work fans out and joins;
- Gemini handles bounded ambiguity/synthesis;
- Gemini synthesis produces **proof-carrying structured claims**;
- deterministic code verifies action-relevant record/finding/source references and claim types;
- invalid model output can be repaired automatically within a hard budget;
- final A1 action authorization remains deterministic application policy;
- the event→action→ack hero requires zero human intervention.

Governing rules:

> **Deterministic when the workflow is known; agentic when the decision is ambiguous; dynamic only when the workflow itself cannot reasonably be known in advance.**

> **LLM proposes; deterministic machinery verifies whatever can be verified before the claim may influence autonomous action.**

ADK remains outer infrastructure under Clean Architecture.

---

## 2. Mandatory Pre-Implementation Spike

Before production runtime code, complete `docs/ADK_CAPABILITY_SPIKE.md` against the exact pinned `google-adk` version.

Verify:

- backend/event invocation without interactive chat;
- supported sequential/parallel workflow primitives;
- join/failure semantics;
- structured Gemini output compatible with proof-carrying DTOs;
- session/run identifiers;
- resume/recovery capabilities;
- callbacks;
- eval/observability path;
- deterministic application verifier can execute outside model authority.

If workshop class names differ from shipping Python APIs, preserve architecture using the documented fallback ladder. Do not invent APIs.

---

## 3. Clean Architecture Boundary

```text
Google ADK / Gemini
        ↓
infrastructure orchestration adapter
        ↓
application workflow / ports
        ↓
domain + deterministic policy
```

Forbidden:

```text
domain -> google.adk
application -> concrete Gemini/ADK SDK
ADK stage -> raw Firestore business mutation
ADK stage -> direct notification provider
Gemini -> claim-verification policy
Gemini -> action authorization
ADK stage -> duplicated scientific/domain calculation
```

---

## 4. Canonical Hero Runtime

```text
surveillance.signal.detected
          ↓
create/load incident
          ↓
FUNCTION: get_incident_context
          ↓
      FAN OUT
  ├─ FUNCTION: compare_resistance_profiles
  ├─ FUNCTION: get_baseline_summary
  └─ FUNCTION: get_missing_fields
          ↓
         JOIN
          ↓
AGENT: bounded investigation triage
          ↓
EvidenceSearchPort
          ↓
AGENT: proof-carrying evidence-grounded synthesis
          ↓
FUNCTION: verify_reasoning_claims
   ├─ invalid → AGENT: bounded repair → verify again
   └─ repair exhausted → abstain
          ↓
FUNCTION: package/schema validation
          ↓
FUNCTION: autonomy/action policy
   ├─ A1 eligible → continue
   └─ blocked/insufficient → abstain
          ↓
FUNCTION: freshness revalidation
          ↓
FUNCTION: transactional ActionIntent / idempotency reservation
          ↓
APPLICATION/ADAPTER: real A1 external action
          ↓
EVENT/CALLBACK: machine acknowledgement
          ↓
FUNCTION: completion state transition
```

The hero path has **no clarification or human approval stage**.

---

## 5. Function / Deterministic Stages

Known mandatory work must not be agent-selected optional tools.

Deterministic stages include:

- context load;
- profile comparison;
- baseline summary;
- structural missingness;
- fixed state/event routing;
- deterministic finding ID/version generation;
- proof-carrying record/finding/source reference verification;
- claim-type policy and forbidden-claim checks;
- package/schema validation;
- action class A0/A1/A2/A3;
- allow-list/authorization checks;
- freshness/material-change check;
- ActionIntent/outbox/idempotency;
- acknowledgement transition.

Gemini must not be called merely to execute fixed policy.

---

## 6. Gemini Agent Stages

Gemini may:

- reason across joined findings;
- select bounded approved-evidence intent when ambiguous;
- produce labelled hypotheses;
- synthesize structured proof-carrying claims/package;
- repair model output from structured verifier errors;
- stop with uncertainty when evidence is insufficient.

Gemini may not:

- calculate surveillance facts that ordinary code owns;
- fabricate missing canonical data;
- invent authoritative record/finding/source IDs;
- waive proof-verification errors;
- promote a hypothesis to fact by changing prose/claim type;
- decide final action class/authorization;
- send external action directly;
- diagnose/prescribe/confirm outbreak.

---

## 7. Proof-Carrying Structured Output

Agent output must be parseable into typed application DTOs equivalent to:

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

Claim types include at least:

```text
OBSERVED_FACT
DERIVED_FINDING
EVIDENCE_STATEMENT
HYPOTHESIS
ACTION_JUSTIFICATION
```

Forbidden autonomous-v0.1 claim classes include diagnosis, prescription, outbreak confirmation, mandatory containment authority, and official public-health declaration.

See `docs/PROOF_CARRYING_REASONING.md`.

---

## 8. Deterministic Claim Verification

After synthesis and before action eligibility:

```text
VerifyReasoningClaims(
  incident_id,
  incident_version,
  package_version,
  claims,
  canonical_context,
  deterministic_findings,
  approved_evidence_manifest,
  policy_version
) -> ClaimVerificationReport
```

Verifier checks:

- canonical record IDs exist and belong to current incident;
- deterministic finding IDs exist, match current run/version, and support declared derived values;
- evidence/source IDs were actually retrieved and approved;
- package/finding/source versions are not stale;
- observed facts do not rely solely on model inference;
- hypotheses remain hypotheses;
- forbidden claim types/wording are rejected;
- required uncertainty/limitations are present where policy requires them;
- model output cannot authorize A1/A2/A3.

Unknown or unsupported references are deterministic failures.

---

## 9. Hero Missing-Data Behavior

The hero fixture is complete enough for A1 completion.

Outside the hero:

```text
material missing data
→ NEEDS_INFORMATION
→ autonomous abstention
```

No required human-input primitive belongs in the hero runtime.

Human pause/resume may remain a secondary/future evaluation capability if needed, but must not weaken Taskmaster proof.

---

## 10. Automatic Repair Loop

Proof/package verification returns structured errors.

```text
invalid proof-carrying package
→ structured verification errors
→ Gemini repair using existing permitted facts/findings/evidence
→ deterministic verifier
```

Requirements:

- hard `max_reasoning_repair_attempts` / package repair budget (target `2`);
- each attempt traceable;
- model cannot waive verifier;
- repair cannot mutate canonical facts/deterministic findings/action policy;
- new evidence may be added only through explicit approved retrieval path;
- exhausted budget → `VALIDATION_FAILED` / abstention;
- invalid/unverified package never reaches autonomy policy/action.

---

## 11. Tool / Capability Boundary

Application-facing capabilities may include:

```text
get_incident_context
compare_resistance_profiles
get_baseline_summary
get_missing_fields
search_approved_guidance
synthesize_proof_carrying_package / agent contract
verify_reasoning_claims
validate_incident_package
classify_autonomous_action
revalidate_incident_before_action
prepare_action_intent
```

Not every capability is an agent tool. Most mandatory deterministic capabilities are workflow/function stages.

No arbitrary shell, unrestricted DB, arbitrary URL evidence, or direct notification tool.

---

## 12. External Action Boundary

The model/ADK agent does not own external side effects.

```text
application workflow
→ verified package prerequisite
→ deterministic A1 policy
→ freshness
→ transactional ActionIntent/outbox
→ NotificationPort
→ authorized A1 infrastructure adapter
→ external target
```

Machine acknowledgement returns through a protected interface/event adapter into an application acknowledgement use case.

---

## 13. State / Execution Identity

Persist/correlate where useful:

```text
incident_id
event_id
correlation_id
graph_run_id
agent_session_id
agent_invocation_id
agent_run_id
attempt
package_version
source_watermark
claim_count
claim_verification_status
verification_error_codes
reasoning_repair_attempt_count
action_class
autonomy_policy_result
action_intent_id
idempotency_reference
delivery_id
acknowledgement_id
```

Firestore/application persistence remains canonical workflow truth.

ADK session/checkpoint is execution continuity only.

---

## 14. Resumability

Use stable supported ADK resume/session primitives where they help.

Recover from:

- process restart;
- model/evidence transient failure;
- Pub/Sub redelivery;
- proof-repair interruption;
- external send/ack transient failure.

On recovery:

1. load canonical state;
2. rebuild current context;
3. restore execution refs if useful;
4. rerun safe/idempotent stages as required;
5. re-run proof verification if source/package context changed;
6. freshness before external action.

No checkpoint bypasses proof verification, freshness, or idempotency.

---

## 15. Context Compaction / Memory

May compact non-authoritative execution narration.

Canonical facts, deterministic outputs, proof references, source IDs, package/action versions, delivery/ack state remain in application persistence and are reconstructed.

Long-term model memory is not factual AMR authority for v0.1.

Private chain-of-thought is not persisted as canonical incident evidence.

---

## 16. Callbacks

Callbacks/interceptors may support:

- telemetry;
- context preparation;
- execution budgets;
- redaction;
- invoking application freshness checks.

Callbacks do not own hidden business/action/proof policy.

---

## 17. Model / Tool / Time Budgets

Configure explicit limits:

- model-call count;
- tool/capability count;
- reasoning repair attempts;
- retries;
- wall-clock timeout.

A failure to complete within budget results in visible bounded failure/abstention.

---

## 18. Evaluation

### Hero trajectory

Assert:

```text
0 user prompts
0 human interventions
0 clarifications
0 approvals
required deterministic stages executed
bounded Gemini stages executed
proof-carrying claims produced
claim verification passed
A1 policy accepted
freshness passed
1 logical ActionIntent
1 external effect
1 machine acknowledgement
```

### Proof/safety

Evaluate:

- unknown canonical record reference;
- unknown deterministic finding reference;
- wrong-run/stale finding reference;
- unknown/unretrieved approved source;
- unsupported observed/derived claim;
- hypothesis→fact escalation;
- forbidden claim type;
- proof verification failure blocks A1;
- repair success/exhaustion;
- `unsafe_claim_escape_rate == 0` on committed adversarial software suite.

Do not call that clinical validation.

### Runtime/action

Evaluate:

- required branch failure;
- branch-order independence;
- fixed router zero model call;
- prompt injection;
- no-evidence behavior;
- A2/A3 block;
- non-allow-listed target block;
- stale recompute;
- duplicate event/side-effect suppression;
- crash/retry around external action;
- restart/recovery;
- session context conflict loses to canonical state.

---

## 19. Observability

Emit safe execution facts:

```text
INVESTIGATION_GRAPH_STARTED
FUNCTION_NODE_STARTED/COMPLETED
PARALLEL_FANOUT_STARTED
PARALLEL_BRANCH_COMPLETED
PARALLEL_JOIN_COMPLETED
AGENT_NODE_STARTED/COMPLETED
EVIDENCE_SEARCH_COMPLETED
REASONING_PACKAGE_GENERATED
CLAIM_VERIFICATION_STARTED/PASSED/FAILED
REASONING_REPAIR_STARTED/COMPLETED/EXHAUSTED
AUTONOMY_POLICY_EVALUATED
FRESHNESS_CHECK_STARTED/PASSED/FAILED
ACTION_INTENT_PREPARED
IDEMPOTENCY_RESERVED
NOTIFICATION_SENT
NOTIFICATION_ACKNOWLEDGED
WORKFLOW_COMPLETED/ABSTAINED
```

No private chain-of-thought.

---

## 20. Production Rules

- ADK Web local-only;
- production event entrypoints protected;
- external ack endpoint protected/authenticated as appropriate;
- secrets injected;
- Cloud Run min/max/cost controls;
- hosted/judged release stable;
- exact versions recorded.

---

## 21. Definition of Done

- [ ] capability spike passed;
- [ ] exact ADK version pinned;
- [ ] event starts workflow without chat;
- [ ] deterministic stages mandatory and model-free;
- [ ] parallel/join semantics proven;
- [ ] proof-carrying structured output implemented;
- [ ] deterministic verifier implemented inward of ADK/Gemini;
- [ ] fabricated/stale/forbidden claims blocked;
- [ ] hero has no human interaction;
- [ ] proof/package repair bounded;
- [ ] A1 policy deterministic;
- [ ] A2/A3 blocked;
- [ ] freshness + ActionIntent/idempotency mandatory;
- [ ] real external action outside model tool access;
- [ ] machine acknowledgement closes flow;
- [ ] resume/context/eval/observability behavior proven.
