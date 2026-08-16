# ADR 0005 — Graph-First Hybrid Orchestration with Google ADK

**Status:** Accepted  
**Date:** 2026-08-16

## Context

Ngabo already separates deterministic AMR/surveillance logic from agentic reasoning. The official All Things Agentic hackathon workshop on multi-agent orchestration adds a more precise implementation model for Google ADK: use deterministic function/workflow nodes when behavior is known, agent nodes only when model reasoning is useful, parallel fan-out/join for independent work, deterministic routers for exhaustive rules, collaborative agents for selectively invoking specialist reasoning, and dynamic workflows only when execution topology cannot be known ahead of time.

The earlier Ngabo agent contract allowed the model to choose tools broadly. That is safe when tools are bounded, but it still gives Gemini unnecessary control over steps that Ngabo already knows should execute for every investigation. This can increase model calls, latency, token cost, and nondeterminism without improving the result.

## Decision

Ngabo v0.1 will use a **graph-first hybrid orchestration pattern**.

The governing architecture rule is:

> **Deterministic when the workflow is known; agentic when the decision is ambiguous; dynamic only when the workflow itself cannot reasonably be known in advance.**

### Core investigation graph

The v0.1 graph will:

1. load canonical incident context;
2. fan out independent deterministic investigation calculations;
3. join those results;
4. use Gemini for bounded triage/reasoning;
5. retrieve approved evidence through `EvidenceSearchPort`;
6. pause/resume for targeted clarification when needed;
7. use Gemini for evidence-grounded synthesis;
8. validate the package deterministically;
9. stop at the human approval gate before consequential action.

Core deterministic fan-out candidates are:

- resistance-profile comparison;
- baseline summary;
- missing-field assessment.

Evidence retrieval may be parallelized only when the query can be formed deterministically from canonical context. Otherwise the agent first chooses a bounded evidence-search intent.

### Routing

Use deterministic routing for:

- event dispatch;
- state-policy decisions;
- validation outcomes;
- duplicate/idempotency paths;
- approval/rejection action paths;
- retry policy where rules are explicit.

Use agentic routing only for bounded ambiguous choices such as which optional evidence topic or specialist capability is relevant.

### Collaborative agents

A specialist-agent topology is not required for v0.1. Add specialist agents only when evaluation shows a real benefit in capability, traceability, or separation of expertise. When used, the coordinator should invoke only the relevant subset rather than all specialists.

### Dynamic workflows

Runtime-generated dynamic workflow topology is deferred from the core v0.1 path. It may be appropriate later for open-ended research, genomics, or investigations whose execution tree cannot be known in advance.

## Clean Architecture Consequence

ADK graph primitives remain infrastructure/runtime implementation details.

```text
ADK workflow/function/agent nodes
              ↓
infrastructure orchestration adapter
              ↓
application contracts / ports / use cases
              ↓
domain policy + deterministic services
```

A function node is not permission to bypass application/domain boundaries.

## Consequences

### Positive

- fewer unnecessary LLM calls;
- lower latency and token cost;
- more deterministic behavior;
- clearer separation between scientific computation and model reasoning;
- easier unit and trajectory testing;
- stronger observability;
- clearer hackathon architecture/demo story;
- preserves agent autonomy where it actually matters.

### Costs / Risks

- graph orchestration introduces explicit workflow code;
- parallel fan-out requires typed failure/join semantics;
- the exact ADK graph APIs must be confirmed against the installed version;
- over-constraining the graph could reduce useful flexibility if optional investigations become more complex later.

## Guardrails

- Do not move domain logic into ADK nodes.
- Do not invoke Gemini for fixed rules or reproducible calculations.
- Do not introduce multiple agents merely to display a multi-agent diagram.
- Do not introduce runtime-dynamic topology for the core v0.1 path without a concrete requirement and architecture review.
- Parallelism must remain safe, read-only where possible, and observable.
- Required branch failures must remain visible and cannot be hidden by later model synthesis.
- Human approval and external-action safety boundaries remain unchanged.
- Implement against the exact installed ADK version; workshop terminology does not override actual library APIs.

## Validation

The canonical seeded scenario should record:

- model-call count;
- deterministic/function-node call count;
- branch timings;
- join timing;
- agentic routing/tool choices;
- clarification count;
- retries/resumes;
- total investigation duration.

These are engineering regression metrics, not clinical performance metrics.

## References

- `docs/ORCHESTRATION_PATTERNS.md`
- `docs/ADK_RUNTIME.md`
- `docs/AGENT_ARCHITECTURE.md`
- `docs/SYSTEM_DESIGN.md`
- All Things Agentic Hackathon resources: https://allthingsagentichackathon.devpost.com/resources
