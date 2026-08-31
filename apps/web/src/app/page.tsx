// Ngabo web console — Issue #90 live-status skeleton.
//
// Server component: reads the ngabo-core readiness/version payload at request
// time through the approved API boundary (CORE_API_URL) and renders an
// honest IN DEVELOPMENT / SYNTHETIC status panel. The Connect timeline renders
// only persisted workflow events and the current server-reported active stage;
// it never invents progress or implies clinical validation.
//
// State handling is explicit and honest:
//   - missing config (no CORE_API_URL)  -> MISSING_CONFIG
//   - unreachable / error response      -> DEGRADED
//   - malformed payload / identity drift -> SCHEMA_MISMATCH
//   - complete, matching typed identity -> LIVE
//
// The component is force-dynamic so the payload is fetched at request time,
// never baked into the image at build time (which would fabricate a status).

import type { Metadata } from "next";
import type { ReactNode } from "react";
import AutoRefresh from "./auto-refresh";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export const metadata: Metadata = {
  title: "Ngabo — AMR Surveillance & Incident Response",
  description:
    "Open-source, event-driven antimicrobial-resistance surveillance and incident-response system.",
};

const FETCH_TIMEOUT_MS = 5000;
const EXPECTED_CORE_SERVICE = "ngabo-core";
const SOURCE_REVISION_RE = /^[0-9a-f]{40}$/;
const IMAGE_DIGEST_RE = /^sha256:[0-9a-f]{64}$/;

type CoreStatus =
  | { kind: "MISSING_CONFIG" }
  | { kind: "DEGRADED"; detail: string }
  | { kind: "SCHEMA_MISMATCH"; detail: string }
  | {
      kind: "LIVE";
      status: "ok";
      service: string;
      version: string;
      revision: string;
      imageDigest: string;
      environment: string;
      ready: true;
    };

interface ReadyPayload {
  status: "ok";
  service: string;
  version: string;
  revision: string;
  ready: true;
}

interface VersionPayload {
  service: string;
  version: string;
  revision: string;
  environment: string;
  image_digest: string;
}

type ConnectEvent = {
  event: string;
  signal_id?: string;
};

type ConnectStatus =
  | { kind: "EMPTY" }
  | { kind: "DEGRADED"; detail: string }
  | {
      kind: "BATCH";
      labId: string;
      receivedCount: number;
      acceptedCount: number;
      quarantinedCount: number;
      signalId: string;
      events: ConnectEvent[];
      outcome: string;
      activeStage?: string;
      workflowState: string;
      deliveryId?: string;
      ackId?: string;
    };

const EVENT_LABELS: Record<string, string> = {
  LAB_BATCH_SYNCED: "Laboratory export received",
  CLEANING_STARTED: "Deterministic cleaning started",
  VALIDATION_COMPLETED: "Records validated",
  NORMALIZATION_COMPLETED: "Accepted records standardized",
  QUARANTINE_COMPLETED: "Invalid records quarantined safely",
  SURVEILLANCE_REFRESHED: "Surveillance state refreshed",
  SIGNAL_DETECTED: "Meaningful resistance signal detected",
  INVESTIGATION_STARTED: "Autonomous investigation started",
  WORKFLOW_HERO_COMPLETED: "Evidence verified and coordination acknowledged",
  WORKFLOW_BLOCKED: "Workflow stopped safely",
};

const WORKFLOW_STAGES = [
  { event: "LAB_BATCH_SYNCED", active: "Receiving the laboratory export" },
  { event: "CLEANING_STARTED", active: "Cleaning the laboratory records" },
  { event: "VALIDATION_COMPLETED", active: "Validating required surveillance fields" },
  { event: "NORMALIZATION_COMPLETED", active: "Standardizing accepted records" },
  { event: "QUARANTINE_COMPLETED", active: "Separating records that need review" },
  { event: "SURVEILLANCE_REFRESHED", active: "Refreshing canonical surveillance state" },
  { event: "SIGNAL_DETECTED", active: "Evaluating resistance signals" },
  { event: "INVESTIGATION_STARTED", active: "Loading the governed investigation context" },
  {
    event: "WORKFLOW_HERO_COMPLETED",
    active: "Grounding evidence, verifying claims and coordinating safely",
  },
] as const;

function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

function isReadyPayload(value: unknown): value is ReadyPayload {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  return (
    record.status === "ok" &&
    record.service === EXPECTED_CORE_SERVICE &&
    isNonEmptyString(record.version) &&
    typeof record.revision === "string" &&
    SOURCE_REVISION_RE.test(record.revision) &&
    record.ready === true
  );
}

function isVersionPayload(value: unknown): value is VersionPayload {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  return (
    record.service === EXPECTED_CORE_SERVICE &&
    isNonEmptyString(record.version) &&
    typeof record.revision === "string" &&
    SOURCE_REVISION_RE.test(record.revision) &&
    isNonEmptyString(record.environment) &&
    typeof record.image_digest === "string" &&
    IMAGE_DIGEST_RE.test(record.image_digest)
  );
}

function identityMatches(ready: ReadyPayload, version: VersionPayload): boolean {
  return (
    ready.service === version.service &&
    ready.version === version.version &&
    ready.revision === version.revision
  );
}

// Google ID token acquisition for the authenticated web→core boundary.
// ngabo-core is private on Cloud Run; the web runtime identity (which holds
// run.invoker on the core service) must present an audience-matched Google
// ID token. On Cloud Run this is available from the metadata server; when it
// is absent (local dev), requests proceed unauthenticated and any 403
// degrades honestly to DEGRADED.
const GOOGLE_METADATA_BASE = "http://metadata.google.internal";
const METADATA_FLAVOR_HEADER = "Metadata-Flavor";
const METADATA_FLAVOR_VALUE = "Google";
const ID_TOKEN_PATH =
  "/computeMetadata/v1/instance/service-accounts/default/identity";

async function acquireGoogleIdToken(audience: string): Promise<string | null> {
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
    try {
      const response = await fetch(
        `${GOOGLE_METADATA_BASE}${ID_TOKEN_PATH}?audience=${encodeURIComponent(
          audience,
        )}`,
        {
          signal: controller.signal,
          headers: {
            [METADATA_FLAVOR_HEADER]: METADATA_FLAVOR_VALUE,
          },
        },
      );
      if (!response.ok) return null;
      const token = await response.text();
      return token.trim().length > 0 ? token.trim() : null;
    } finally {
      clearTimeout(timer);
    }
  } catch {
    return null;
  }
}

async function fetchJson(
  coreApiUrl: string,
  path: string,
): Promise<unknown> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    const token = await acquireGoogleIdToken(coreApiUrl);
    const headers: Record<string, string> = { Accept: "application/json" };
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
    const response = await fetch(`${coreApiUrl}${path}`, {
      signal: controller.signal,
      cache: "no-store",
      headers,
    });
    if (!response.ok) {
      throw new Error(`${path} returned HTTP ${response.status}`);
    }
    return await response.json();
  } finally {
    clearTimeout(timer);
  }
}

async function fetchCoreStatus(): Promise<CoreStatus> {
  const coreApiUrl = process.env.CORE_API_URL ?? "";
  if (!coreApiUrl) {
    return { kind: "MISSING_CONFIG" };
  }
  try {
    const [readyRaw, versionRaw] = await Promise.all([
      fetchJson(coreApiUrl, "/ready"),
      fetchJson(coreApiUrl, "/version"),
    ]);
    if (!isReadyPayload(readyRaw)) {
      return {
        kind: "SCHEMA_MISMATCH",
        detail: "incomplete or invalid /ready contract",
      };
    }
    if (!isVersionPayload(versionRaw)) {
      return {
        kind: "SCHEMA_MISMATCH",
        detail: "incomplete or invalid /version identity",
      };
    }
    if (!identityMatches(readyRaw, versionRaw)) {
      return {
        kind: "SCHEMA_MISMATCH",
        detail: "/ready and /version runtime identity do not match",
      };
    }
    return {
      kind: "LIVE",
      status: readyRaw.status,
      service: readyRaw.service,
      version: readyRaw.version,
      revision: readyRaw.revision,
      imageDigest: versionRaw.image_digest,
      environment: versionRaw.environment,
      ready: true,
    };
  } catch (error) {
    const detail =
      error instanceof Error ? error.message : "network error contacting core";
    return { kind: "DEGRADED", detail };
  }
}

function asNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function parseConnectStatus(value: unknown): ConnectStatus {
  if (typeof value !== "object" || value === null) {
    return { kind: "DEGRADED", detail: "invalid /connect/status payload" };
  }
  const record = value as Record<string, unknown>;
  if (record.status === "none") return { kind: "EMPTY" };
  const hero = record.hero_result;
  const heroRecord =
    typeof hero === "object" && hero !== null
      ? (hero as Record<string, unknown>)
      : {};
  const events = Array.isArray(record.events)
    ? record.events.flatMap((event): ConnectEvent[] => {
        if (typeof event !== "object" || event === null) return [];
        const candidate = event as Record<string, unknown>;
        if (!isNonEmptyString(candidate.event)) return [];
        return [
          {
            event: candidate.event,
            ...(isNonEmptyString(candidate.signal_id)
              ? { signal_id: candidate.signal_id }
              : {}),
          },
        ];
      })
    : [];
  const receivedCount = asNumber(record.received_count);
  const acceptedCount = asNumber(record.accepted_count);
  const quarantinedCount = asNumber(record.quarantined_count);
  const activeStage = isNonEmptyString(record.active_stage)
    ? record.active_stage
    : undefined;
  if (
    !isNonEmptyString(record.lab_id) ||
    receivedCount === null ||
    acceptedCount === null ||
    quarantinedCount === null ||
    (events.length === 0 && activeStage === undefined)
  ) {
    return { kind: "DEGRADED", detail: "incomplete /connect/status payload" };
  }
  return {
    kind: "BATCH",
    labId: record.lab_id,
    receivedCount,
    acceptedCount,
    quarantinedCount,
    signalId: isNonEmptyString(record.signal_id) ? record.signal_id : "none",
    events,
    outcome: isNonEmptyString(heroRecord.outcome)
      ? heroRecord.outcome
      : "IN_PROGRESS",
    ...(activeStage ? { activeStage } : {}),
    workflowState: isNonEmptyString(record.workflow_state)
      ? record.workflow_state
      : "RUNNING",
    ...(isNonEmptyString(heroRecord.delivery_id)
      ? { deliveryId: heroRecord.delivery_id }
      : {}),
    ...(isNonEmptyString(heroRecord.ack_id) ? { ackId: heroRecord.ack_id } : {}),
  };
}

async function fetchConnectStatus(): Promise<ConnectStatus> {
  const coreApiUrl = process.env.CORE_API_URL ?? "";
  if (!coreApiUrl) return { kind: "EMPTY" };
  try {
    return parseConnectStatus(await fetchJson(coreApiUrl, "/connect/status"));
  } catch (error) {
    return {
      kind: "DEGRADED",
      detail: error instanceof Error ? error.message : "status request failed",
    };
  }
}

function StatusPanel({ status }: { status: CoreStatus }) {
  const badge = "rounded border px-2 py-0.5 font-mono text-xs";
  switch (status.kind) {
    case "MISSING_CONFIG":
      return (
        <section
          aria-label="core status"
          className="mx-auto max-w-2xl rounded-lg border border-amber-300 bg-amber-50 p-6 text-left dark:border-amber-700 dark:bg-amber-950/30"
        >
          <p className="mb-2 font-semibold text-amber-800 dark:text-amber-200">
            <span className={`${badge} border-amber-500 bg-amber-100`}>
              MISSING CONFIG
            </span>{" "}
            ngabo-core URL not configured
          </p>
          <p className="text-sm leading-6 text-amber-800/80 dark:text-amber-200/80">
            This deployment has no <code>CORE_API_URL</code>. The web console
            cannot show live backend state until the core service URL is
            provided (Cloud Run deploy sets it automatically). No local
            process is required once configured.
          </p>
        </section>
      );
    case "DEGRADED":
      return (
        <section
          aria-label="core status"
          className="mx-auto max-w-2xl rounded-lg border border-orange-300 bg-orange-50 p-6 text-left dark:border-orange-700 dark:bg-orange-950/30"
        >
          <p className="mb-2 font-semibold text-orange-800 dark:text-orange-200">
            <span className={`${badge} border-orange-500 bg-orange-100`}>
              DEGRADED
            </span>{" "}
            ngabo-core unreachable
          </p>
          <p className="text-sm leading-6 text-orange-800/80 dark:text-orange-200/80">
            The core service did not respond: <code>{status.detail}</code>.
            This is honest degraded state — nothing is fabricated while the
            backend recovers.
          </p>
        </section>
      );
    case "SCHEMA_MISMATCH":
      return (
        <section
          aria-label="core status"
          className="mx-auto max-w-2xl rounded-lg border border-red-300 bg-red-50 p-6 text-left dark:border-red-700 dark:bg-red-950/30"
        >
          <p className="mb-2 font-semibold text-red-800 dark:text-red-200">
            <span className={`${badge} border-red-500 bg-red-100`}>
              SCHEMA MISMATCH
            </span>{" "}
            unexpected core payload
          </p>
          <p className="text-sm leading-6 text-red-800/80 dark:text-red-200/80">
            The core responded but the payload identity is incomplete or
            inconsistent (<code>{status.detail}</code>). The console refuses
            to render guessed values.
          </p>
        </section>
      );
    case "LIVE":
      return (
        <section
          aria-label="core status"
          className="mx-auto max-w-2xl rounded-lg border border-emerald-300 bg-emerald-50 p-6 text-left dark:border-emerald-700 dark:bg-emerald-950/30"
        >
          <p className="mb-2 font-semibold text-emerald-800 dark:text-emerald-200">
            <span className={`${badge} border-emerald-500 bg-emerald-100`}>
              LIVE
            </span>{" "}
            ngabo-core reachable
          </p>
          <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
            <dt className="text-emerald-800/60 dark:text-emerald-200/60">status</dt>
            <dd className="font-mono text-emerald-900 dark:text-emerald-100">
              {status.status}
            </dd>
            <dt className="text-emerald-800/60 dark:text-emerald-200/60">service</dt>
            <dd className="font-mono text-emerald-900 dark:text-emerald-100">
              {status.service}
            </dd>
            <dt className="text-emerald-800/60 dark:text-emerald-200/60">version</dt>
            <dd className="font-mono text-emerald-900 dark:text-emerald-100">
              {status.version}
            </dd>
            <dt className="text-emerald-800/60 dark:text-emerald-200/60">revision</dt>
            <dd className="break-all font-mono text-emerald-900 dark:text-emerald-100">
              {status.revision}
            </dd>
            <dt className="text-emerald-800/60 dark:text-emerald-200/60">image digest</dt>
            <dd className="break-all font-mono text-emerald-900 dark:text-emerald-100">
              {status.imageDigest}
            </dd>
            <dt className="text-emerald-800/60 dark:text-emerald-200/60">environment</dt>
            <dd className="font-mono text-emerald-900 dark:text-emerald-100">
              {status.environment}
            </dd>
            <dt className="text-emerald-800/60 dark:text-emerald-200/60">ready</dt>
            <dd className="font-mono text-emerald-900 dark:text-emerald-100">
              true
            </dd>
          </dl>
        </section>
      );
  }
}

function ConnectTimeline({ status }: { status: ConnectStatus }) {
  if (status.kind === "EMPTY") {
    return (
      <section className="mx-auto max-w-4xl rounded-2xl border border-zinc-200 bg-white p-7 text-left shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-violet-600">
          Live surveillance workflow
        </p>
        <h2 className="mt-2 text-2xl font-semibold">Waiting for a laboratory export</h2>
        <p className="mt-2 text-sm text-zinc-500">
          Choose the watched folder in Ngabo Connect, then add the synthetic CSV.
          Real workflow events will appear here automatically.
        </p>
      </section>
    );
  }
  if (status.kind === "DEGRADED") {
    return (
      <section className="mx-auto max-w-4xl rounded-2xl border border-orange-300 bg-orange-50 p-7 text-left">
        <h2 className="text-xl font-semibold text-orange-900">Timeline unavailable</h2>
        <p className="mt-2 text-sm text-orange-800">{status.detail}</p>
      </section>
    );
  }
  const completed = status.outcome === "HERO_COMPLETED";
  const completedEvents = new Set(status.events.map((event) => event.event));
  const completedStages = WORKFLOW_STAGES.filter((stage) =>
    completedEvents.has(stage.event),
  ).length;
  const progress = Math.round(
    ((completedStages + (status.activeStage ? 0.5 : 0)) /
      WORKFLOW_STAGES.length) *
      100,
  );
  return (
    <section className="mx-auto max-w-4xl rounded-2xl border border-zinc-200 bg-white p-7 text-left shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-violet-600">
            Live surveillance workflow
          </p>
          <h2 className="mt-2 text-2xl font-semibold">{status.labId}</h2>
          <p className="mt-1 font-mono text-xs text-zinc-500">Signal {status.signalId}</p>
        </div>
        <span className={`rounded-full px-3 py-1 font-mono text-xs font-semibold ${completed ? "bg-emerald-100 text-emerald-800" : "bg-violet-100 text-violet-800"}`}>
          {status.outcome.replaceAll("_", " ")}
        </span>
      </div>
      <div className="mt-6 grid grid-cols-3 gap-3 text-center">
        <Metric label="received" value={status.receivedCount} />
        <Metric label="accepted" value={status.acceptedCount} />
        <Metric label="quarantined" value={status.quarantinedCount} />
      </div>
      <div className="mt-7">
        <div className="mb-2 flex items-center justify-between text-xs font-medium text-zinc-500">
          <span>{completed ? "Workflow complete" : "Autonomous workflow in progress"}</span>
          <span>{Math.min(progress, 100)}%</span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800">
          <div
            className={`h-full rounded-full transition-all duration-700 ${completed ? "bg-emerald-500" : "bg-violet-600"}`}
            style={{ width: `${Math.min(progress, 100)}%` }}
          />
        </div>
      </div>
      <ol className="mt-7 space-y-3">
        {WORKFLOW_STAGES.map((stage, index) => {
          const isDone = completedEvents.has(stage.event);
          const isActive = status.activeStage === stage.event;
          return (
            <li
              key={stage.event}
              className={`relative overflow-hidden rounded-xl border px-4 py-3 transition-all duration-500 ${
                isDone
                  ? "border-emerald-200 bg-emerald-50/70 dark:border-emerald-900 dark:bg-emerald-950/20"
                  : isActive
                    ? "border-violet-400 bg-violet-50 shadow-md shadow-violet-100 dark:bg-violet-950/30 dark:shadow-none"
                    : "border-zinc-200 bg-zinc-50 opacity-55 dark:border-zinc-800 dark:bg-zinc-900"
              }`}
            >
              {isActive ? (
                <div className="absolute inset-x-0 bottom-0 h-1 overflow-hidden bg-violet-100 dark:bg-violet-950">
                  <div className="h-full w-1/2 animate-pulse rounded-full bg-violet-600" />
                </div>
              ) : null}
              <div className="flex items-center gap-3">
                {isDone ? (
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-500 text-sm font-bold text-white">✓</span>
                ) : isActive ? (
                  <span
                    aria-label={`${stage.event} in progress`}
                    className="h-8 w-8 shrink-0 animate-spin rounded-full border-4 border-violet-200 border-t-violet-600"
                  />
                ) : (
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-zinc-300 text-xs font-semibold text-zinc-400">
                    {index + 1}
                  </span>
                )}
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="font-medium">
                      {isActive ? stage.active : EVENT_LABELS[stage.event]}
                    </p>
                    <span className={`text-[10px] font-semibold uppercase tracking-wider ${isDone ? "text-emerald-700" : isActive ? "text-violet-700" : "text-zinc-400"}`}>
                      {isDone ? "Complete" : isActive ? "Working" : "Pending"}
                    </span>
                  </div>
                  <p className="mt-0.5 font-mono text-[11px] text-zinc-500">{stage.event}</p>
                </div>
              </div>
            </li>
          );
        })}
      </ol>
      {completed && status.deliveryId && status.ackId ? (
        <div className="mt-6 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
          <p className="font-semibold">Safe external coordination completed</p>
          <p className="mt-1 font-mono text-xs">delivery {status.deliveryId}</p>
          <p className="font-mono text-xs">machine acknowledgement {status.ackId}</p>
          <p className="mt-2 font-semibold">0 prompts · 0 approvals · 0 human interventions</p>
        </div>
      ) : null}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl bg-zinc-100 p-3 dark:bg-zinc-900">
      <p className="text-2xl font-semibold">{value}</p>
      <p className="text-xs uppercase tracking-wide text-zinc-500">{label}</p>
    </div>
  );
}

export default async function Home(): Promise<ReactNode> {
  const [status, connectStatus] = await Promise.all([
    fetchCoreStatus(),
    fetchConnectStatus(),
  ]);
  return (
    <main className="flex min-h-screen flex-col items-center gap-6 bg-background px-6 py-12 text-center text-foreground">
      <AutoRefresh />
      <h1 className="text-5xl font-semibold tracking-tight">Ngabo</h1>
      <p className="max-w-xl text-lg leading-8 text-zinc-600 dark:text-zinc-400">
        An open-source, event-driven antimicrobial-resistance surveillance and
        incident-response system.
      </p>
      <div className="w-full">
        <StatusPanel status={status} />
      </div>
      <div className="w-full">
        <ConnectTimeline status={connectStatus} />
      </div>
      <p className="text-sm text-zinc-500 dark:text-zinc-400">
        Current status:{" "}
        <code className="rounded bg-black/[.06] px-1.5 py-0.5 font-mono text-[0.9em] dark:bg-white/[.08]">
          v0.1.0
        </code>{" "}
        <span className="rounded bg-violet-100 px-1.5 py-0.5 font-mono text-[0.85em] text-violet-800 dark:bg-violet-900/40 dark:text-violet-200">
          IN DEVELOPMENT — SYNTHETIC
        </span>
      </p>
    </main>
  );
}
