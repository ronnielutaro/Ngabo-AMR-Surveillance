# ngabo-core

Python service implementing Ngabo's AMR surveillance and incident-response core
using Clean Architecture. Dependencies point inward:

```text
infrastructure -> interfaces -> application -> domain
```

## Layout

```text
ngabo/
├── domain/           # entities, value objects, deterministic scientific policy
├── application/      # use cases, workflows, ports
├── interfaces/       # HTTP/event translation
├── infrastructure/   # framework/vendor adapters (FastAPI, GCP, ADK, Gemini)
└── bootstrap/        # composition root + health entry point
```

**Status:** M1A scaffold. The layers exist as importable packages; no product
behavior is implemented yet (see GitHub Issue #12).

## Development

```bash
uv sync                    # create the environment and install dev tooling
uv run pytest              # run tests
uv run ruff check .        # lint
uv run mypy ngabo tests    # type check
uv run ngabo-health        # print the scaffold health payload
```

Root-level equivalents are available via `pnpm core:install`, `pnpm core:test`,
`pnpm core:lint`, `pnpm core:typecheck`, and `pnpm core:health`.
