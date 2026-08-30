import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import Home from "./page";

// Home is a force-dynamic async server component; each test controls
// CORE_API_URL and the global fetch response.
const ORIGINAL_CORE_API_URL = process.env.CORE_API_URL;

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
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            status: "ok",
            service: "ngabo-core",
            version: "0.1.0",
            revision: "a".repeat(40),
            environment: "test",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );
    const html = renderToStaticMarkup(await Home());
    expect(html).toContain("Ngabo");
  });

  it("states synthetic/in-development boundary without claiming product behavior", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            status: "ok",
            service: "ngabo-core",
            version: "0.1.0",
            revision: "a".repeat(40),
            environment: "test",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );
    const html = renderToStaticMarkup(await Home());
    expect(html).toContain("IN DEVELOPMENT — SYNTHETIC");
    expect(html).not.toContain("detected");
    expect(html).not.toContain("outbreak");
  });

  it("shows live backend-derived values when core is reachable", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            status: "ok",
            service: "ngabo-core",
            version: "0.1.0",
            revision: "abc123".repeat(7),
            environment: "test",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );
    const html = renderToStaticMarkup(await Home());
    expect(html).toContain("LIVE");
    expect(html).toContain("ngabo-core");
    expect(html).toContain("0.1.0");
    expect(html).toContain("abc123".repeat(7));
    expect(html).toContain("test");
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
      vi.fn().mockResolvedValue(new Response("boom", { status: 503 })),
    );
    const html = renderToStaticMarkup(await Home());
    expect(html).toContain("DEGRADED");
    expect(html).toContain("503");
  });

  it("renders schema mismatch when the payload shape is unexpected", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({ message: "hello" }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );
    const html = renderToStaticMarkup(await Home());
    expect(html).toContain("SCHEMA MISMATCH");
  });
});
