# Gitflow Integration Policy

The governance baseline is established on `main`. Active implementation work should use `develop` as the next-release integration branch.

```text
main
  ↑ release / hotfix
  │
develop
  ↑ feature PRs
  │
feature/*
```

See `CONTRIBUTING.md` for the authoritative branch lifecycle.
