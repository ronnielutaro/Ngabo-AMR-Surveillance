import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import Home from "./page";

describe("Home", () => {
  it("renders the Ngabo identity heading", () => {
    const html = renderToStaticMarkup(Home());
    expect(html).toContain("Ngabo");
  });

  it("states maturity without claiming shipped product behavior", () => {
    const html = renderToStaticMarkup(Home());
    expect(html).toContain("hackathon MVP in development");
  });
});
