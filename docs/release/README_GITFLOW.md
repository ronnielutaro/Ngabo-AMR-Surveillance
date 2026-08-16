# Gitflow Handoff Note

The repository governance baseline was established on `main` before active feature implementation begins.

The next implementation step should initialize/use `develop` as the integration branch, after which feature work follows `feature/* -> develop`, releases follow `release/vX.Y.Z -> main + develop`, and urgent fixes follow `hotfix/vX.Y.Z -> main + develop`.
