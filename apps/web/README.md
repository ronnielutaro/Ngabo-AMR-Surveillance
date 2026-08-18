# ngabo-web

Frontend application for Ngabo — the incident-response console.

**Current status:** `v0.1.0` hackathon MVP in development — M1A scaffold only.
No product behavior is implemented yet (see GitHub Issue #12).

## Stack

- Next.js (App Router) + TypeScript
- Tailwind CSS v4
- Vitest
- pnpm workspace member (`ngabo-web`)

## Commands

From the repository root:

- `pnpm web:dev` — start the dev server
- `pnpm web:lint` — ESLint
- `pnpm web:typecheck` — TypeScript (`tsc --noEmit`)
- `pnpm web:test` — Vitest
- `pnpm web:build` — production build
