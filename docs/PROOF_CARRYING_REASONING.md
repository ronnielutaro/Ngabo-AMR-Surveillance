# Ngabo — Proof-Carrying Reasoning & Deterministic Claim Verification

**Status:** Required v0.1 agent-safety and reasoning contract  
**Date:** 2026-08-17  
**Applies to:** Gemini reasoning/synthesis nodes, incident packages, package validation, autonomous A1 action eligibility, evaluation, observability and demo claims

---

## 1. Decision

Ngabo must never trust an LLM-generated factual, evidentiary, or action-relevant statement merely because it is fluent, confident, or internally reasoned.

The governing rule is:

> **LLM proposes; deterministic machinery verifies whatever can be verified before the claim may influence autonomous action.**

Gemini may reason over canonical facts, deterministic findings and approved evidence, but any actionable output must be represented as **proof-carrying structured claims** whose references can be checked against Ngabo's canonical state and approved evidence graph.

Hidden/private chain-of-thought is not an Ngabo safety primitive, is not persisted as canonical evidence, and must not be exposed in the UI, logs or submission. Where more inference-time reasoning is useful, use bounded internal reasoning, optional self-consistency, or multiple candidate generation only as a quality technique; downstream authority still comes from machine-verifiable outputs.

---

## 2. Why This Exists

Ngabo's zero-human Taskmaster hero requires stronger safeguards than a workflow that relies on a person to catch a hallucination before action.

Prompting alone cannot guarantee that a model will not:

- invent an isolate identifier;
- misstate a deterministic calculation;
- cite a source that was never retrieved;
- overstate a hypothesis as an observed fact;
- omit a material uncertainty;
- produce language that crosses into diagnosis, prescription or outbreak confirmation;
- recommend an action class that exceeds the permitted autonomous envelope.

The solution is not to ask the model to "think harder" and trust the answer. The solution is to make model output **referentially accountable** to data and evidence that ordinary code can check.

---

## 3. Truth and Authority Hierarchy

For v0.1, authority flows in this order:

```text
canonical source facts
        ↓
deterministic scientific calculations
        ↓
approved retrieved evidence
        ↓
verified structured model claims
        ↓
labelled hypotheses / synthesis
        ↓
deterministic action policy
        ↓
freshness + idempotency
        ↓
A1 autonomous coordination action
```

An LLM statement never outranks the source object, deterministic calculation, approved source or deterministic policy it references.

---

## 4. Claim Taxonomy

Every material model claim in the incident package must have an explicit type.

### `OBSERVED_FACT`

A statement directly supported by canonical source data.

Required proof:

- one or more canonical record IDs;
- exact field/value provenance where practical;
- no model-created factual value.

Example:

```text
"Three Klebsiella pneumoniae isolates were recorded in Ward A during the current surveillance window."
```

The verifier checks that the referenced isolates exist and that the statement is structurally consistent with canonical values.

### `DERIVED_FINDING`

A statement supported by deterministic Ngabo computation.

Required proof:

- deterministic finding/result ID;
- calculation/policy version;
- referenced inputs;
- output value used by the claim.

Examples:

- resistance-profile similarity;
- baseline deviation;
- temporal concentration;
- ward concentration;
- structural missingness;
- detector score/trigger reason.

Gemini must not recompute these values from prose.

### `EVIDENCE_STATEMENT`

A statement grounded in approved retrieved guidance or evidence.

Required proof:

- approved `source_id`;
- retrieved chunk/excerpt/reference ID where applicable;
- provenance/version metadata;
- support relation to the statement.

A URL invented by the model is never sufficient.

### `HYPOTHESIS`

An interpretation that is not directly established as fact.

Required proof:

- supporting observed/derived claim IDs;
- supporting evidence IDs where relevant;
- explicit uncertainty;
- contradicting/alternative evidence when known;
- `claim_type = HYPOTHESIS` preserved through presentation.

A hypothesis may not be silently promoted to observed fact, diagnosis, prescription or confirmed outbreak.

### `ACTION_JUSTIFICATION`

A structured explanation of why a candidate A1 coordination action is useful.

Required proof:

- verified upstream claim IDs only;
- requested action class;
- target/purpose metadata.

This claim does **not** authorize the action. `AutonomousActionPolicy` remains deterministic and owns A0/A1/A2/A3 classification and authorization.

### Forbidden v0.1 claim types

The autonomous public v0.1 path must reject output attempting to assert:

- `DIAGNOSIS`;
- `PRESCRIPTION`;
- `OUTBREAK_CONFIRMATION`;
- `MANDATORY_CONTAINMENT_ORDER`;
- `OFFICIAL_PUBLIC_HEALTH_DECLARATION`.

These are outside the current autonomous authority envelope regardless of model confidence or reasoning quality.

---

## 5. Canonical Structured Claim Schema

Implementation may evolve field names, but the semantic contract must remain equivalent.

```json
{
  "claim_id": "claim-01",
  "claim_type": "HYPOTHESIS",
  "statement": "The isolates show a closely matching resistance phenotype consistent with a possible shared epidemiologic process.",
  "supporting_record_ids": ["ISO-031", "ISO-034", "ISO-039"],
  "supporting_finding_ids": ["profile-comparison-17"],
  "supporting_source_ids": ["GUIDANCE-004"],
  "contradicting_claim_ids": [],
  "uncertainties": ["Genomic relatedness is unavailable."],
  "requested_action_class": "A1",
  "confidence_label": "BOUNDED_HYPOTHESIS"
}
```

Rules:

- IDs must be opaque references generated/owned by Ngabo, not free-form invented references;
- confidence labels are descriptive and must not masquerade as calibrated probabilities unless a calibrated model actually produced them;
- model text cannot create authority by choosing a more powerful `claim_type` or `requested_action_class`;
- unknown references fail verification.

---

## 6. Deterministic Claim Verifier

After Gemini synthesis and before package/action eligibility, run a deterministic verifier.

Conceptual interface:

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

The verifier must check, at minimum:

### Referential integrity

- every isolate/record ID exists in the current incident context;
- every deterministic finding ID exists and belongs to the current incident/run;
- every evidence/source ID was actually retrieved and is approved;
- no stale package/result version is being used.

### Type integrity

- observed facts do not rely only on model inference;
- derived findings map to deterministic outputs;
- hypotheses stay labelled as hypotheses;
- forbidden claim types are rejected;
- A1 justification cannot itself authorize A1.

### Content/policy integrity

- prohibited diagnosis/prescription/outbreak-confirmation language is absent;
- unsupported observed/derived statements are rejected;
- required uncertainties/limitations are present where policy demands them;
- evidence statements cannot cite unapproved/unretrieved sources;
- the package remains within the public v0.1 intended-use boundary.

### Freshness integrity

Claim verification is package-version scoped. A later material source change may invalidate a previously verified package even if the individual references remain syntactically valid.

Pre-action freshness validation still runs after proof verification.

---

## 7. Verification Report

The verifier returns structured errors rather than prose-only rejection.

Example:

```json
{
  "valid": false,
  "errors": [
    {
      "code": "UNKNOWN_FINDING_REFERENCE",
      "claim_id": "claim-03",
      "reference": "baseline-999"
    },
    {
      "code": "UNSUPPORTED_FACTUAL_ASSERTION",
      "claim_id": "claim-04",
      "field": "statement"
    }
  ]
}
```

Error codes should be stable enough for deterministic routing and evaluation.

---

## 8. Bounded Automatic Repair

For repairable model-output failures:

```text
Gemini structured package
        ↓
proof/claim verifier
        ↓
invalid
        ↓
structured verification errors
        ↓
Gemini repair using only existing canonical facts/findings/evidence
        ↓
verify again
```

Required controls:

- hard repair-attempt budget;
- repair may not retrieve arbitrary new evidence unless the graph explicitly routes through the approved retrieval capability;
- repair may not mutate canonical source facts or deterministic findings;
- repair may not change action policy;
- all attempts are observable as metadata;
- if still invalid after budget: `VALIDATION_FAILED` / autonomous abstention / no A1 action.

Suggested v0.1 default:

```text
max_reasoning_repair_attempts = 2
```

---

## 9. Relationship to Chain-of-Thought / Deliberation

Ngabo may use model-native reasoning capabilities internally where supported and beneficial, but:

- hidden chain-of-thought is not stored as incident truth;
- hidden chain-of-thought is not shown in the UI;
- hidden chain-of-thought is not required for a judge to trust the system;
- verbalized reasoning is not treated as evidence;
- a detailed explanation does not bypass verification;
- model confidence does not authorize action.

If self-consistency or multiple-candidate inference is introduced, disagreement should increase uncertainty or trigger abstention rather than being hidden.

A consensus of model outputs is still not proof; all selected claims must pass deterministic verification.

---

## 10. Graph Integration

The canonical v0.1 graph becomes:

```text
signal
 ↓
deterministic context + fan-out/join
 ↓
Gemini triage
 ↓
approved evidence retrieval
 ↓
Gemini proof-carrying synthesis
 ↓
FUNCTION: deterministic claim/proof verification
 ↓
valid?
 ├─ no → bounded repair → verify again
 │         └─ exhausted → autonomous abstention
 └─ yes
 ↓
FUNCTION: autonomous action policy
 ↓
FUNCTION: freshness
 ↓
ActionIntent / outbox
 ↓
A1 external action
 ↓
machine acknowledgement
```

The verifier belongs in the deterministic/application/domain side of the architecture. ADK/Gemini must not own the verification policy.

---

## 11. Clean Architecture Placement

Recommended inward contracts:

```text
application/
  use_cases/
    verify_reasoning_claims.py
  ports/
    evidence_manifest_port.py
  dto/
    reasoning_claim.py
    claim_verification_report.py

domain/
  services/
    claim_policy.py
  value_objects/
    claim_type.py
    evidence_reference.py
```

Outer infrastructure may parse Gemini output into application DTOs, but the policy deciding whether references/claim types are valid must not depend on Gemini, ADK, Firestore or FastAPI classes.

**Incident package contract (#52).** `IncidentPackageCandidate`
(`application/value_objects/incident_package.py`) is the framework-free,
versioned proposal contract that sits between the deterministic investigation
capabilities + approved evidence retrieval + Gemini synthesis (upstream) and
`VerifyReasoningClaims` (downstream). It reuses the #28 claim/reference types
and carries package/incident/source-watermark identity plus descriptive policy
and model metadata. It is a **candidate/proposal only**: it is structurally
incapable of declaring itself verified, approved, or action-authorized, and no
verification/report state (see §7) exists inside the proposed package.
Verification and authorization outcomes are produced downstream — never by the
model-proposed package.

---

## 12. Observability

Record public-safe metadata such as:

```text
REASONING_PACKAGE_GENERATED
CLAIM_VERIFICATION_STARTED
CLAIM_VERIFICATION_PASSED
CLAIM_VERIFICATION_FAILED
REASONING_REPAIR_STARTED
REASONING_REPAIR_COMPLETED
REASONING_REPAIR_EXHAUSTED
AUTONOMOUS_ABSTENTION
```

Useful fields:

```text
incident_id
incident_version
package_version
claim_count
claim_type_counts
invalid_reference_count
unsupported_claim_count
repair_attempt
verification_error_codes
```

Do not log private chain-of-thought.

---

## 13. Evaluation Contract

Add committed tests/evals for:

### Reference fabrication

- unknown isolate ID;
- unknown deterministic finding ID;
- unknown/unretrieved source ID;
- source from wrong incident/run;
- stale package/finding reference.

### Claim-type escalation

- hypothesis mislabeled as observed fact;
- attempted `DIAGNOSIS`;
- attempted `PRESCRIPTION`;
- attempted `OUTBREAK_CONFIRMATION`;
- attempted A2/A3 authorization via model output.

### Evidence integrity

- retrieved source does not support claimed statement;
- citation omitted for evidence statement;
- fabricated URL/source title;
- contradictory evidence omitted where policy requires it.

### Repair behavior

- repair succeeds from structured verifier errors;
- repair remains within existing evidence/facts;
- repair budget is enforced;
- repeated invalid output abstains safely.

### Action coupling

- no A1 action when claim verification fails;
- no A1 action when required proof references are missing;
- no A1 action from an unverified package;
- verified package still requires deterministic action policy + freshness + idempotency.

Required public metrics where meaningful:

```text
unsupported_claim_rate
invalid_reference_rate
fabricated_source_rate
fabricated_record_rate
claim_verification_pass_rate
repair_success_rate
repair_attempt_count
unsafe_claim_escape_rate
```

For the committed adversarial suite, target:

```text
unsafe_claim_escape_rate == 0
```

Do not present that software-test target as a clinical safety guarantee.

---

## 14. UI / Demo Contract

The product may expose:

- claim type;
- supporting record/finding/source references;
- uncertainty/limitations;
- `Verified` / `Verification failed` state;
- repair attempt metadata in a technical view.

It must not expose private chain-of-thought.

A strong demo explanation is:

> **Gemini can generate hypotheses and synthesis, but Ngabo does not trust free-form model prose. Every action-relevant claim must point back to canonical records, deterministic calculations or approved evidence and pass machine verification before it can enter the autonomous action path.**

---

## 15. Non-Goals

v0.1 does not claim:

- formal mathematical proof of medical truth;
- clinical validation of model reasoning;
- diagnosis/prescribing authority;
- universal hallucination elimination;
- that self-consistency equals correctness;
- that deterministic validators can verify every semantic medical assertion.

For claims whose correctness cannot be sufficiently verified within the v0.1 policy, the safe result is uncertainty or abstention.

---

## 16. Definition of Done

This capability is complete only when:

- [ ] Gemini synthesis returns typed proof-carrying claims;
- [ ] referenced canonical records/findings/evidence are machine-checkable;
- [ ] deterministic claim verification is implemented inward of ADK/Gemini;
- [ ] forbidden claim types cannot enter the autonomous path;
- [ ] bounded repair is implemented and budgeted;
- [ ] exhausted repair causes no external A1 action;
- [ ] proof verification is tested independently of Gemini;
- [ ] adversarial fabricated-reference/claim-escalation tests pass;
- [ ] `unsafe_claim_escape_rate == 0` on the committed software adversarial suite;
- [ ] observability exposes verification results without chain-of-thought;
- [ ] `EVALUATION.md` reports measured results before the submission claims this capability.
