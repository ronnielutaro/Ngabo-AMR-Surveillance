import path from "path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // Issue #89 container contract: emit the self-contained standalone output
  // used by the production ngabo-web image (apps/web/Dockerfile). The trace
  // root is the pnpm workspace root; with the hoisted node_modules layout
  // the traced tree contains real files, so the standalone output is
  // complete.
  output: "standalone",
  outputFileTracingRoot: path.join(__dirname, "../../"),
  // Deterministic build ID so the standalone output (and therefore the image
  // digest) is byte-identical for the same source commit. The Docker build
  // supplies NGABO_SOURCE_REVISION; outside the container the SHA is absent
  // and a stable constant is used (never a per-build random value).
  generateBuildId: () =>
    process.env.NGABO_SOURCE_REVISION ?? "ngabo-web-local",
};

export default nextConfig;
