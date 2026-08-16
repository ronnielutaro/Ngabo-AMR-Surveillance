# Ngabo — Autonomous Effect Outbox & Exactly-Once-Intent Contract

**Status:** Required v0.1 external-action reliability contract  
**Date:** 2026-08-16

---

## 1. Problem

A zero-human agent must be safer under failures than a manually supervised demo.

The dangerous failure window is:

```text
Ngabo decides to act
→ external request succeeds
→ process crashes before local state records success
→ retry sends again
```

Pub/Sub itself is at-least-once, Cloud Run can restart, and network responses can be ambiguous. “Just retry” is not sufficient for autonomous side effects.

---

## 2. Decision

Use a **transactional effect-intent/outbox pattern** for every autonomous A1 external action.

The objective is not mathematically guaranteed exactly-once delivery across arbitrary third-party systems. The objective is **exactly-once Ngabo intent plus idempotent external execution** wherever the provider/receiver supports it.

---

## 3. Action Intent

Before sending externally, create an immutable/persisted `ActionIntent` inside a Firestore transaction or equivalent atomic application operation.

Suggested fields:

```text
action_intent_id
incident_id
incident_version
package_id
package_version
source_watermark
action_class
autonomy_policy_version
target_id
payload_hash
idempotency_key
status
attempt_count
created_at
last_attempt_at
delivery_id
acknowledgement_id
last_error
```

Allowed status lifecycle:

```text
PREPARED
→ SENDING
→ SENT
→ ACKNOWLEDGED

or

PREPARED/SENDING
→ RETRYABLE_FAILURE
→ SENDING

or

PREPARED
→ CANCELLED_STALE

or

* → TERMINAL_FAILURE
```

---

## 4. Transactional Preparation

The preparation transaction must atomically verify:

- incident/package versions still match;
- source watermark still current;
- autonomy policy result is A1;
- destination is allow-listed/authorized;
- no active/completed equivalent intent exists;
- idempotency key is unique for the logical effect.

Then persist `ActionIntent(PREPARED)`.

This creates a durable **commit point for intent** before external execution.

---

## 5. Idempotency Key

Derive a stable key from the logical effect, for example:

```text
hash(
  incident_id,
  package_version,
  action_type,
  target_id,
  payload_hash
)
```

The exact construction may differ, but retrying the same logical effect must reuse the same key.

Do not generate a new random idempotency key on every retry.

---

## 6. Dispatcher

A bounded dispatcher consumes/prepares pending intents and calls `NotificationPort`.

```text
ActionIntent PREPARED
→ mark/lease SENDING
→ external adapter(idempotency_key, payload)
→ persist provider delivery ID/result
→ SENT
```

Requirements:

- lease/compare-and-set prevents two workers concurrently sending same intent;
- retryable error keeps same logical intent/key;
- terminal error is visible;
- crash/restart can safely rediscover pending intent.

---

## 7. External Receiver / Provider Contract

Preferred hackathon endpoint supports deduplication using Ngabo's idempotency key.

Receiver stores:

```text
idempotency_key
first_received_at
payload_hash
delivery_id
ack_status
```

If the same key is received again, receiver returns the existing delivery result rather than creating a second logical effect.

This dramatically reduces the ambiguous-crash duplicate risk.

---

## 8. Machine Acknowledgement

After external receipt/processing:

```text
external endpoint
→ signed/authenticated acknowledgement callback/event
→ Ngabo acknowledgement adapter
→ application use case
→ ActionIntent ACKNOWLEDGED
→ incident completion
```

Acknowledgement contains at least:

```text
action_intent_id or idempotency_key
delivery_id
acknowledgement_id
status
timestamp
integrity/authentication proof where applicable
```

Ack replay is idempotent.

---

## 9. Freshness Race Protection

Freshness is checked when preparing the intent.

If canonical data changes **before the intent is durably prepared**, no send.

If data changes **after PREPARED but before send**, the dispatcher/application policy should re-check whether the intent remains executable before first external send.

If stale:

```text
PREPARED
→ CANCELLED_STALE
→ recompute/revalidate/package/policy
→ new ActionIntent if still eligible
```

Once a real external effect has already been sent, new data does not rewrite history; create a follow-up workflow/action if appropriate.

---

## 10. Payload Immutability

The payload referenced by an `ActionIntent` must be immutable for that intent.

Persist/hash the exact sent payload.

A changed package/payload requires a **new logical intent** after freshness/policy checks, not mutation of the old prepared action.

---

## 11. Clean Architecture

Suggested boundaries:

```text
Application
  PrepareAutonomousAction
  DispatchPreparedAction
  RecordActionDelivery
  RecordActionAcknowledgement

Ports
  ActionIntentRepository
  NotificationPort

Infrastructure
  FirestoreActionIntentRepository
  AuthorizedWebhookNotificationAdapter
  Ack HTTP/PubSub adapter
```

No ADK/Gemini stage directly sends externally.

---

## 12. Security

- action targets configured/allow-listed, never arbitrary model URLs;
- ack endpoint authenticated/signed where practical;
- secrets injected, never model-visible if avoidable;
- payload contains synthetic demo data only;
- logs store metadata rather than secret tokens;
- rate/retry bounds enforced.

---

## 13. Evaluation

Required tests:

### Duplicate Pub/Sub trigger

Two identical event deliveries produce one logical action intent/effect.

### Crash after external success before local response persistence

Retry reuses same idempotency key; receiver dedupes; Ngabo reconciles delivery state.

### Two dispatchers race

At most one owns/send lease for the intent.

### Stale before first send

Prepared-but-not-sent intent becomes `CANCELLED_STALE`; no stale effect.

### Ack replay

Multiple identical acknowledgements result in one acknowledged logical state.

### Payload mutation

Cannot alter a prepared intent payload; new version requires new intent.

### Unauthorized target

No intent is prepared.

---

## 14. Demo / Architecture Prize Story

This is a strong technical answer to:

> “What happens if your autonomous agent crashes exactly while taking action?”

Answer:

> Ngabo commits an immutable, version-scoped action intent before sending. The external action uses a stable idempotency key, the receiver deduplicates retries, stale unsent intents are cancelled, and a machine acknowledgement closes the effect ledger. The model never owns the side effect.

---

## 15. Definition of Done

- [ ] `ActionIntent` modeled;
- [ ] atomic preparation verifies current A1 eligibility/freshness;
- [ ] stable idempotency key;
- [ ] dispatcher lease/CAS semantics;
- [ ] real adapter propagates idempotency key;
- [ ] test endpoint dedupes same key;
- [ ] delivery result persisted;
- [ ] machine ack authenticated/processed idempotently;
- [ ] stale unsent intent cancelled;
- [ ] crash/race/replay tests pass;
- [ ] hero still completes without human intervention.
