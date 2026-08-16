# ADR 0008 — Transactional Autonomous Effect Outbox

**Status:** Accepted  
**Date:** 2026-08-16

## Context

Ngabo's Taskmaster hero executes a real external A1 coordination action without human supervision. Pub/Sub is at-least-once, Cloud Run can restart, and network responses can be ambiguous. A crash after an external send but before local persistence could otherwise produce duplicate autonomous effects.

## Decision

Use an immutable `ActionIntent` / transactional outbox pattern for v0.1 autonomous external actions.

Before sending, Ngabo atomically verifies current A1 eligibility/freshness and persists a prepared logical action intent containing the package/source versions, target, payload hash and stable idempotency key.

A dispatcher owns/leases that intent, sends through `NotificationPort`, and persists provider delivery state. The external test/sandbox receiver must deduplicate repeated requests using the same idempotency key where possible. Machine acknowledgement closes the intent idempotently.

## Consequences

### Positive

- protects against duplicate autonomous effects under retry/redelivery/crash;
- provides durable proof of exactly one logical Ngabo intent;
- makes external action auditable;
- separates model reasoning from side effects;
- strengthens Best Architectural Design story;
- allows stale unsent intents to be cancelled safely.

### Tradeoffs

- adds an `ActionIntent` state model/repository;
- requires lease/CAS or equivalent dispatcher semantics;
- requires test endpoint support for idempotency/deduplication;
- does not claim impossible universal exactly-once delivery across arbitrary third-party systems.

## Required State

At minimum:

```text
action_intent_id
incident_id/package_version/source_watermark
action_class
target_id
payload_hash
idempotency_key
status/attempt_count
delivery_id
acknowledgement_id
```

## Architecture

```text
PrepareAutonomousAction
→ ActionIntentRepository
→ DispatchPreparedAction
→ NotificationPort
→ external A1 endpoint
→ acknowledgement adapter
→ RecordActionAcknowledgement
```

No Gemini/ADK agent node directly owns the external side effect.

## Tests

- duplicate event → one logical intent/effect;
- two dispatchers race → one send owner;
- crash after receiver success → same idempotency key on retry;
- stale unsent intent → cancelled before send;
- ack replay → one acknowledged state;
- payload mutation requires new intent.

## Reference

See `docs/AUTONOMOUS_EFFECT_OUTBOX.md`.
