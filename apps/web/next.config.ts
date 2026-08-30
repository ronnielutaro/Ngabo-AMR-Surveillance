import path from "path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // Issue #89 container contract: emit the self-contained standalone output
  // used by the production ngabo-web image (apps/web/Dockerfile). The trace
  // root is the pnpm workspace root; with the hoisted node_modules layout
  // (.npmrc) the traced tree contains real files, so the standalone output
  // is complete.
  output: "standalone",
  outputFileTracingRoot: path.join(__dirname, "../../"),
};

export default nextConfig;
