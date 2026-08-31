import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import Home from "./page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh: vi.fn() }),
}));

const ORIGINAL_CORE_API_URL = process.env.CORE_API_URL;
const REVISION = "a".repeat(40);
const DIGEST = "sha256:" + "d".repeat(64);

function okJson(body: unknown) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

function readyBody(
  overrides: Record<string, unknown> = {},
): Record<string, unknown> {
  return {
    status: "ok",
    service: "ngabo-core",
    version: "0.1.0",
    revision: REVISION,
    ready: true,
    ...overrides,
  };
}

function versionBody(
  overrides: Record<string, unknown> = {},
): Record<string, unknown> {
  return {
    service: "ngabo-core",
    version: "0.1.0",
    revision: REVISION,
    environment: "test",
    image_digest: DIGEST,
    ...overrides,
  };
}

function stubCore(
  ready: Record<string, unknown> = readyBody(),
  version: Record<string, unknown> = versionBody(),
  connect: Record<string, unknown> = { status: "none" },
) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation((url: string) => {
      if (url.startsWith("http://metadata.google.internal")) {
        return Promise.resolve(new Response("test-id-token", { status: 200 }));
      }
      if (url.endsWith("/ready")) return Promise.resolve(okJson(ready));
      if (url.endsWith("/version")) return Promise.resolve(okJson(version));
      if (url.endsWith("/connect/status")) return Promise.resolve(okJson(connect));
      return Promise.resolve(new Response("not found", { status: 404 }));
    }),
  );
}

beforeEach(() => {
  process.env.CORE_API_URL = "https://core.example.invalid";
});

afterEach(() => {
  if (ORIGINAL_CORE_API_URL === undefined) {
    delete process.env.CORE_API_URL;
  } else {
    process.env.CORE_API_URL = ORIGINAL_CORE_API_URL;
  }
  vi.unstubAllGlobals();
});

describe("Home", () => {
  it("renders the Ngabo identity heading", async () => {
    stubCore();
    const html = renderToStaticMarkup(await Home());
    expect(html).toContain("Ngabo");
  });

  it("states synthetic/in-development boundary without claiming product behavior", async () => {
    stubCore();
    const html = renderToStaticMarkup(await Home());
    expect(html).toContain("IN DEVELOPMENT — SYNTHETIC");
    expect(html).not.toContain("detected");
    expect(html).not.toContain("outbreak");
  });

  it("shows live backend-derived values only for complete matching identity", async () => {
    stubCore();
    const html = renderToStaticMarkup(await Home());
    expect(html).toContain("LIVE");
    expect(html).toContain("ngabo-core");
    expect(html).toContain("0.1.0");
    expect(html).toContain(REVISION);
    expect(html).toContain(DIGEST);
    expect(html).toContain("test");
    expect(html).toContain("true");
  });

  it("renders only persisted Connect events and acknowledgement identifiers", async () => {
    stubCore(readyBody(), versionBody(), {
      lab_id: "synthetic-lab-gulu",
      received_count: 4,
      accepted_count: 3,
      quarantined_count: 1,
      signal_id: "sig-demo",
      hero_result: {
        outcome: "HERO_COMPLETED",
        delivery_id: "dlv-demo",
        ack_id: "ack-demo",
      },
      events: [
        { event: "LAB_BATCH_SYNCED" },
        { event: "SIGNAL_DETECTED", signal_id: "sig-demo" },
        { event: "WORKFLOW_HERO_COMPLETED" },
      ],
    });
    const html = renderToStaticMarkup(await Home());
    expect(html).toContain("Laboratory export received");
    expect(html).toContain("Meaningful resistance signal detected");
    expect(html).toContain("Evidence verified and coordination acknowledged");
    expect(html).toContain("dlv-demo");
    expect(html).toContain("ack-demo");
    expect(html).toContain("0 prompts · 0 approvals · 0 human interventions");
  });

  it("renders an honest missing-config state when CORE_API_URL is absent", async () => {
    delete process.env.CORE_API_URL;
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);
    const html = renderToStaticMarkup(await Home());
    expect(html).toContain("MISSING CONFIG");
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("renders an honest degraded state when core is unreachable", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new Error("fetch failed: connection refused")),
    );
    const html = renderToStaticMarkup(await Home());
    expect(html).toContain("DEGRADED");
    expect(html).toContain("connection refused");
  });

  it("renders an honest degraded state on non-2xx response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((url: string) => {
        if (url.startsWith("http://metadata.google.internal")) {
          return Promise.resolve(new Response("token", { status: 200 }));
        }
        return Promise.resolve(new Response("boom", { status: 503 }));
      }),
    );
    const html = renderToStaticMarkup(await Home());
    expect(html).toContain("DEGRADED");
    expect(html).toContain("503");
  });

  it("renders schema mismatch when the payload shape is unexpected", async () => {
    stubCore({ message: "hello" }, { message: "hello" });
    const html = renderToStaticMarkup(await Home());
    expect(html).toContain("SCHEMA MISMATCH");
  });
});

describe("Home — fail-closed runtime identity", () => {
  it("rejects missing image_digest", async () => {
    const version = versionBody();
    delete version.image_digest;
    stubCore(readyBody(), version);
    const html = renderToStaticMarkup(await Home());
    expect(html).toContain("SCHEMA MISMATCH");
    expect(html).not.toContain("LIVE");
  });

  it("rejects malformed image_digest", async () => {
    stubCore(readyBody(), versionBody({ image_digest: "latest" }));
    const html = renderToStaticMarkup(await Home());
    expect(html).toContain("SCHEMA MISMATCH");
    expect(html).not.toContain("LIVE");
  });

  it("rejects missing readiness flag", async () => {
    const ready = readyBody();
    delete ready.ready;
    stubCore(ready, versionBody());
    const html = renderToStaticMarkup(await Home());
    expect(html).toContain("SCHEMA MISMATCH");
    expect(html).not.toContain("LIVE");
  });

  it("rejects ready=false", async () => {
    stubCore(readyBody({ ready: false }), versionBody());
    const html = renderToStaticMarkup(await Home());
    expect(html).toContain("SCHEMA MISMATCH");
    expect(html).not.toContain("LIVE");
  });

  it("rejects missing ready revision", async () => {
    const ready = readyBody();
    delete ready.revision;
    stubCore(ready, versionBody());
    const html = renderToStaticMarkup(await Home());
    expect(html).toContain("SCHEMA MISMATCH");
    expect(html).not.toContain("LIVE");
  });

  it("rejects a non-SHA source revision", async () => {
    stubCore(readyBody({ revision: "unknown" }), versionBody({ revision: "unknown" }));
    const html = renderToStaticMarkup(await Home());
    expect(html).toContain("SCHEMA MISMATCH");
    expect(html).not.toContain("LIVE");
  });

  it("rejects revision mismatch between /ready and /version", async () => {
    stubCore(readyBody(), versionBody({ revision: "b".repeat(40) }));
    const html = renderToStaticMarkup(await Home());
    expect(html).toContain("SCHEMA MISMATCH");
    expect(html).not.toContain("LIVE");
  });

  it("rejects version mismatch between /ready and /version", async () => {
    stubCore(readyBody(), versionBody({ version: "0.2.0" }));
    const html = renderToStaticMarkup(await Home());
    expect(html).toContain("SCHEMA MISMATCH");
    expect(html).not.toContain("LIVE");
  });

  it("rejects service mismatch", async () => {
    stubCore(readyBody(), versionBody({ service: "other-core" }));
    const html = renderToStaticMarkup(await Home());
    expect(html).toContain("SCHEMA MISMATCH");
    expect(html).not.toContain("LIVE");
  });
});
