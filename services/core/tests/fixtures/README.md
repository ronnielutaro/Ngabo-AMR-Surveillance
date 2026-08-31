# Event-investigation trace fixtures (Issue #53)

These are **documentation/schema examples** of the secret-free
`EventInvocationResult.to_safe_primitive()` trace produced by the
`EventInvestigationRuntime` outer ADK adapter. They are NOT live outputs and
the IDs are synthetic placeholders (a real run generates fresh opaque
`RUN-<32 hex>` / `ngabo-session-*` / `ngabo-invocation-*` identifiers at the
adapter boundary).

- `event_investigation_trace_success.json` — a
  `COMPLETED_CURRENT_STAGE` success trace (narrow truthful success; no package
  synthesized, no action taken).
- `event_investigation_trace_failure.json` — a `BLOCKED` trace (missing
  incident), proving a failure can never be mislabeled as package completion.

These traces expose outcome, identifiers, safe counters, budget, and error code
only. They never contain isolate records, patient tokens, model deliberation,
credentials, or private chain-of-thought.
