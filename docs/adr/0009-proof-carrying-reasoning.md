# ADR 0009 — Proof-Carrying Reasoning for Model-Generated Claims

**Status:** Accepted  
**Date:** 2026-08-17

## Context

Ngabo's v0.1 Taskmaster hero is intentionally zero-human after the surveillance event. Gemini is useful for bounded interpretation, evidence intent, hypothesis formation, synthesis and repair, but free-form model output can fabricate references, overstate evidence, misclassify hypotheses as facts, or attempt to cross the project's intended-use boundary.

A human reviewer is therefore not an acceptable primary hallucination-control mechanism for the canonical zero-human hero.

The project already follows these principles:

- deterministic where truth can be computed;
- agentic only where ambiguity requires reasoning;
- approved evidence only;
- deterministic A0/A1/A2/A3 action policy;
- autonomous abstention when required facts/evidence are missing;
- freshness and idempotency before A1 action.

A further boundary is required between Gemini synthesis and autonomous action eligibility.

## Decision

Adopt **proof-carrying reasoning** for material model-generated claims.

Gemini must produce typed structured claims that reference the canonical records, deterministic findings and approved evidence used to support them. A deterministic verifier checks those references, claim types and policy constraints before the package can influence the autonomous action path.

Governing rule:

> **LLM proposes; deterministic machinery verifies whatever can be verified before the claim may influence autonomous action.**

The canonical ordering becomes:

```text
canonical facts
→ deterministic findings
→ approved evidence
→ Gemini proof-carrying synthesis
→ deterministic claim verification
→ bounded repair if invalid
→ autonomous action policy
→ freshness
→ ActionIntent/outbox
→ A1 external action
→ machine acknowledgement
```

## Claim types

The v0.1 verifier recognizes at least:

- `OBSERVED_FACT` — must map to canonical source data;
- `DERIVED_FINDING` — must map to deterministic Ngabo output;
- `EVIDENCE_STATEMENT` — must map to approved retrieved evidence;
- `HYPOTHESIS` — must remain explicitly labelled and reference supporting proof/uncertainty;
- `ACTION_JUSTIFICATION` — may explain an A1 candidate action but never authorize it.

The autonomous v0.1 path rejects attempted model claims of:

- diagnosis;
- prescription;
- outbreak confirmation;
- mandatory containment authority;
- official public-health declaration.

## Chain-of-Thought boundary

Private/hidden chain-of-thought is not authoritative evidence, is not persisted as canonical incident truth, and is not exposed in the UI, logs or submission.

Model-native reasoning, self-consistency or multiple-candidate generation may be used as bounded inference-quality techniques, but agreement between model outputs does not bypass deterministic verification.

## Automatic repair

A failed verifier returns structured error codes. Gemini may receive those errors for a bounded repair attempt using only the existing canonical facts/findings/evidence unless the graph separately authorizes approved retrieval.

The repair budget is finite. Exhaustion produces `VALIDATION_FAILED` / autonomous abstention and no A1 action.

## Architecture

Verification policy belongs inward of ADK/Gemini and must be independently testable without model/cloud access.

Recommended application/domain concepts include:

- `ReasoningClaim`;
- `ClaimType`;
- `ClaimVerificationReport`;
- `VerifyReasoningClaims`;
- `ClaimPolicy`.

The verifier may read canonical data/findings/evidence through inward application contracts/ports. It must not delegate verification back to Gemini.

## Evaluation

Committed tests must cover fabricated isolate/finding/source references, claim-type escalation, unsupported factual assertions, stale references, repair budgets and action blocking.

A key software adversarial-suite target is:

```text
unsafe_claim_escape_rate == 0
```

This target must never be represented as clinical validation or a universal hallucination guarantee.

## Consequences

### Positive

- reduces dependence on prompt-following for safety;
- makes model claims auditable and machine-checkable;
- improves the zero-human Taskmaster safety story;
- creates clear evaluation metrics for hallucination/reference integrity;
- reinforces deterministic/agentic separation;
- provides a strong Best Architectural Design narrative.

### Costs

- additional schemas and verifier code;
- more structured-output constraints;
- bounded repair may add latency/model calls;
- semantic support cannot always be proven deterministically, so abstention remains necessary.

## Alternatives considered

### Trust detailed Chain-of-Thought

Rejected. A plausible explanation is not proof, and private chain-of-thought is neither an appropriate product artifact nor an authority mechanism.

### Add a human reviewer to every package

Rejected for the canonical Taskmaster hero because it breaks the zero-human objective and shifts safety burden from engineering to manual supervision.

### Ask a second LLM to judge the first LLM

Insufficient as the primary control. Model consensus may improve reasoning quality but does not provide referential or policy proof.

### Pure deterministic system with no Gemini synthesis

Rejected because bounded hypothesis formation and evidence-grounded synthesis are valuable ambiguous tasks. The correct architecture is hybrid rather than model-free.

## Related documents

- `docs/PROOF_CARRYING_REASONING.md`
- `docs/ORCHESTRATION_PATTERNS.md`
- `docs/TASKMASTER_ZERO_HUMAN_AUTONOMY.md`
- `docs/DATA_SAFETY_EVALUATION.md`
- `docs/AUTONOMOUS_EFFECT_OUTBOX.md`
- ADR 0005, ADR 0007 and ADR 0008
