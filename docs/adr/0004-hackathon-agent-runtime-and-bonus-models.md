# ADR 0004 — Hackathon Agent Runtime & Bonus-Model Strategy

**Status:** Accepted  
**Date:** 2026-08-16

## Context

The All Things Agentic Hackathon rewards more than minimum use of Gemini and Google Cloud. The Taskmaster category explicitly values event-driven autonomous routing and complete multi-step workflows, while the judging rubric emphasizes operational utility, architectural discipline, state management, failure tolerance, proof of action, and production readiness.

Official resources also highlight long-running/resumable ADK workflows, human approval, idempotency, evaluation, observability, scale-to-zero Cloud Run, budget controls, and secure endpoints. Optional bonus contributions include public build content, a qualifying social post, and successfully integrated additional Google AI models such as Gemma.

Ngabo already uses Google ADK, Gemini 3.6 Flash, Cloud Run, Firestore, Pub/Sub, and Cloud Storage. We need to ensure the implementation visibly takes advantage of the hackathon-specific strengths without compromising the project's safety or Clean Architecture.

## Decision

### 1. Taskmaster remains the primary category

Ngabo will be designed and demonstrated as an event-driven autonomous workflow. A new surveillance signal, not a chat prompt, starts the investigation.

### 2. ADK is a runtime capability

The ADK integration will include:

- bounded typed tool orchestration;
- persisted execution/session identifiers;
- resumable agent investigation where supported and stable;
- targeted human-input pause/resume for clarification;
- structured output validation;
- ADK evaluation;
- tracing/observability integration.

Firestore remains the application/workflow source of truth. ADK execution state is complementary, not authoritative business state.

### 3. Consequential approval remains an application/domain gate

Ngabo will not delegate its final safety boundary solely to a framework-level experimental confirmation mechanism. Human review remains an explicit incident state-machine transition.

### 4. A real external action is required for the v0.1 demo

The deterministic demo notification adapter remains for tests, but the hosted/filmed system must execute at least one real authorized external action after approval, through `NotificationPort` and an infrastructure adapter.

### 5. EmbeddingGemma is the planned additional Google AI model

Once the core E2E path is stable, Ngabo will use EmbeddingGemma for semantic retrieval over a curated approved guidance corpus.

The hackathon-scale implementation should use a lightweight in-process similarity index rather than adding a vector database solely for the bonus.

### 6. MedGemma is a gated stretch

MedGemma may be added as a bounded medical-evidence interpretation tool only if:

- the core workflow is already stable;
- its role is source-traceable;
- evaluation shows a useful contribution;
- it does not create clinical overclaiming or deployment risk.

No bonus will be claimed unless the integration is real and demonstrated.

### 7. Multimodal AST/report ingestion is a post-core stretch

Gemini multimodal extraction may create a draft structured record from an image/PDF, but a human must verify the draft before canonical ingestion.

### 8. Public content bonuses are planned deliverables

The LinkedIn build article and social post are part of submission readiness. They must satisfy the exact official hackathon wording/hashtag requirements at publication time.

### 9. Cost/security guidance becomes acceptance criteria

Cloud Run scale-to-zero, max-instance caps, budget alerts, secret isolation, protected expensive/internal endpoints, and cleanup planning are required deployment tasks.

## Clean Architecture Consequences

All new model/framework integrations remain outer adapters:

```text
Domain
  ↑
Application ports/use cases
  ↑
Infrastructure adapters
  ├── Google ADK / Gemini
  ├── EmbeddingGemma
  ├── optional MedGemma
  ├── Firestore
  ├── Pub/Sub
  ├── GCS
  └── notification provider
```

The domain must remain testable without Google SDKs, model calls, or cloud credentials.

## Consequences

### Positive

- stronger Taskmaster fit;
- visible long-running/autonomous-agent behavior;
- stronger Best Architectural Design story;
- better evidence retrieval;
- more credible evaluation and observability;
- stronger proof of action;
- meaningful bonus-point path without architecture theater.

### Costs / Risks

- resumability introduces retry/idempotency complexity;
- real notification integration needs authorized credentials and failure handling;
- EmbeddingGemma adds packaging/runtime work;
- MedGemma or multimodal features can distract from core execution if started too early;
- excessive observability can create privacy/logging risk if message content is captured indiscriminately.

## Guardrails

- Core E2E workflow comes before bonus models.
- EmbeddingGemma comes after core green.
- MedGemma and multimodal ingestion are stretch goals.
- No bonus claim without successful integration and demo evidence.
- No new model may bypass the human safety gate.
- No model may own deterministic scientific calculations.
- No framework feature may become the sole source of business/workflow truth.

## References

- https://allthingsagentichackathon.devpost.com/rules
- https://allthingsagentichackathon.devpost.com/resources
- https://google.github.io/adk-docs/
- https://google.github.io/agents-cli/
- https://ai.google.dev/gemma/docs/embeddinggemma
- https://developers.google.com/health-ai-developer-foundations/medgemma
