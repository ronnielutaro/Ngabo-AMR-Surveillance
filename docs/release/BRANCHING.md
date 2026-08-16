# Gitflow Branch Summary

```text
main
  └── released / release-ready history

develop
  └── integration for the next release

feature/<name>
  └── branch from develop -> PR to develop

release/vX.Y.Z
  └── branch from develop -> main + back to develop

hotfix/vX.Y.Z
  └── branch from main -> main + develop
```

See `CONTRIBUTING.md` and `docs/RELEASE_POLICY.md` for full rules.
