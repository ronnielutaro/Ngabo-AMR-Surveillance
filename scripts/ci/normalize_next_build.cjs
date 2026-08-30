#!/usr/bin/env node
// Deterministic Next.js build output normalizer (Issue #89 reproducibility).
//
// Next.js 16.3.1 embeds per-build random values in its output:
//   - prerender-manifest.json        -> preview.previewModeId,
//                                       preview.previewModeSigningKey,
//                                       preview.previewModeEncryptionKey
//   - server/server-reference-manifest.{js,json} -> "encryptionKey" (base64)
// The values are generated with crypto.randomBytes on every fresh build
// (Next disables its preview-key cache inside containers via is-docker), so
// two builds of the same commit produce different bytes in these three files
// even with SOURCE_DATE_EPOCH + rewrite-timestamp normalization.
//
// This script deterministically derives those keys from the source revision
// (commit SHA) and rewrites every occurrence in the build output. Same
// commit -> same keys -> byte-identical image digest. The derived keys are
// not credentials: preview mode is a build-time server capability and the
// values are published in the image itself; derivation is for reproducibility
// only.
//
// Usage: node scripts/ci/normalize_next_build.cjs <dist-dir> <source-revision>

"use strict";

const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

const [distDir, revision] = process.argv.slice(2);
if (!distDir || !revision) {
  console.error(
    "usage: normalize_next_build.cjs <next-dist-dir> <source-revision>"
  );
  process.exit(2);
}

function sha256Hex(seed) {
  return crypto.createHash("sha256").update(seed).digest("hex");
}

// Same lengths as Next's random generation: previewModeId = 16 bytes,
// signing/encryption keys = 32 bytes (hex in the manifest, base64 in the
// server-reference-manifest).
const previewModeId = sha256Hex(`${revision}:previewModeId`).slice(0, 32);
const previewModeSigningKey = sha256Hex(`${revision}:previewModeSigningKey`);
const previewModeEncryptionKey = sha256Hex(
  `${revision}:previewModeEncryptionKey`
);
const encryptionKeyBase64 = Buffer.from(previewModeEncryptionKey, "hex").toString(
  "base64"
);

const ENCRYPTION_KEY_RE = /("encryptionKey":\s*")[^"]*(")/g;

function walk(dir) {
  const entries = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      entries.push(...walk(full));
    } else {
      entries.push(full);
    }
  }
  return entries;
}

let rewritten = 0;
for (const file of walk(distDir)) {
  if (file.endsWith("prerender-manifest.json")) {
    const manifest = JSON.parse(fs.readFileSync(file, "utf8"));
    if (!manifest.preview) continue;
    manifest.preview.previewModeId = previewModeId;
    manifest.preview.previewModeSigningKey = previewModeSigningKey;
    manifest.preview.previewModeEncryptionKey = previewModeEncryptionKey;
    fs.writeFileSync(file, JSON.stringify(manifest, null, 2) + "\n");
    rewritten += 1;
  } else if (/\.(js|json)$/.test(file)) {
    let text = fs.readFileSync(file, "utf8");
    const next = text.replace(
      ENCRYPTION_KEY_RE,
      `$1${encryptionKeyBase64}$2`
    );
    if (next !== text) {
      fs.writeFileSync(file, next);
      rewritten += 1;
    }
  }
}

console.log(
  `normalize_next_build: ${rewritten} file(s) rewritten for revision ${revision.slice(
    0,
    12
  )}`
);
