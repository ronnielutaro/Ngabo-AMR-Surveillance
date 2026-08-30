// Ngabo web console — Issue #90 live-status skeleton.
//
// Server component: reads the ngabo-core health/version payload at request
// time through the approved API boundary (CORE_API_URL) and renders an
// honest IN DEVELOPMENT / SYNTHETIC status panel. It must never imply AMR
// detection, proof verification, autonomous action, or clinical validation
// exists — the hero workflow is not implemented.
//
// State handling is explicit and honest:
//   - missing config (no CORE_API_URL)  -> MISSING_CONFIG
//   - unreachable / error response      -> DEGRADED
//   - malformed payload / schema drift  -> SCHEMA_MISMATCH
//   - valid typed payload               -> LIVE
//
// The component is force-dynamic so the payload is fetched at request time,
// never baked into the image at build time (which would fabricate a status).

import type { Metadata } from "next";
import type { ReactNode } from "react";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export const metadata: Metadata = {
  title: "Ngabo — AMR Surveillance & Incident Response",
  description:
    "Open-source, event-driven antimicrobial-resistance surveillance and incident-response system.",
};

const FETCH_TIMEOUT_MS = 5000;

type CoreStatus =
  | { kind: "MISSING_CONFIG" }
  | { kind: "DEGRADED"; detail: string }
  | { kind: "SCHEMA_MISMATCH"; detail: string }
  | {
      kind: "LIVE";
      status: string;
      service: string;
      version: string;
      revision: string;
      environment: string;
      ready: boolean;
    };

interface CorePayload {
  status: string;
  service: string;
  version?: string;
  revision?: string;
  environment?: string;
  ready?: boolean;
}

function isCorePayload(value: unknown): value is CorePayload {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  return (
    typeof record.status === "string" &&
    typeof record.service === "string"
  );
}

async function fetchCoreStatus(): Promise<CoreStatus> {
  // Read at call time so tests (and config changes) take effect per render.
  const coreApiUrl = process.env.CORE_API_URL ?? "";
  if (!coreApiUrl) {
    return { kind: "MISSING_CONFIG" };
  }
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
    let response: Response;
    try {
      response = await fetch(`${coreApiUrl}/health`, {
        signal: controller.signal,
        cache: "no-store",
        headers: { Accept: "application/json" },
      });
    } finally {
      clearTimeout(timer);
    }
    if (!response.ok) {
      return {
        kind: "DEGRADED",
        detail: `core /health returned HTTP ${response.status}`,
      };
    }
    const payload: unknown = await response.json();
    if (!isCorePayload(payload)) {
      return { kind: "SCHEMA_MISMATCH", detail: "unexpected core payload shape" };
    }
    return {
      kind: "LIVE",
      status: payload.status,
      service: payload.service,
      version: payload.version ?? "unknown",
      revision: payload.revision ?? "unknown",
      environment: payload.environment ?? "unknown",
      ready: payload.ready ?? false,
    };
  } catch (error) {
    const detail =
      error instanceof Error ? error.message : "network error contacting core";
    return { kind: "DEGRADED", detail };
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
            The core responded but the payload shape is unexpected (
            <code>{status.detail}</code>). The console refuses to render
            guessed values.
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
            <dt className="text-emerald-800/60 dark:text-emerald-200/60">environment</dt>
            <dd className="font-mono text-emerald-900 dark:text-emerald-100">
              {status.environment}
            </dd>
            <dt className="text-emerald-800/60 dark:text-emerald-200/60">ready</dt>
            <dd className="font-mono text-emerald-900 dark:text-emerald-100">
              {status.ready ? "true" : "false"}
            </dd>
          </dl>
        </section>
      );
  }
}

export default async function Home(): Promise<ReactNode> {
  const status = await fetchCoreStatus();
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 bg-background px-8 text-center text-foreground">
      <h1 className="text-5xl font-semibold tracking-tight">Ngabo</h1>
      <p className="max-w-xl text-lg leading-8 text-zinc-600 dark:text-zinc-400">
        An open-source, event-driven antimicrobial-resistance surveillance and
        incident-response system.
      </p>
      <div className="w-full">
        <StatusPanel status={status} />
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
