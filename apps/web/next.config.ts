import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // Issue #89 container contract: emit the self-contained standalone output
  // used by the production ngabo-web image (apps/web/Dockerfile).
  output: "standalone",
};

export default nextConfig;
