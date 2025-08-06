# Release

Releases are triggered by commits with the `chore(release):` prefix on the `main` branch.

## Standard release

Version is bumped automatically based on conventional commits:

```bash
git commit --allow-empty -m "chore(release): release a new version"
```

## Stable release

Bumps the major version (e.g. `0.x.x` -> `1.0.0`):

```bash
git commit --allow-empty -m "chore(release): release a stable version"
```

## Workflow

1. Checks if commit matches `chore(release): ...`
2. Detects `stable` keyword for major version bump
3. Waits for CI to pass (lint, typecheck, unit tests, BDD tests)
4. Bumps version with commitizen (major bump if stable)
5. Generates changelog
6. Creates GitHub release
7. Publishes CLI to PyPI
8. Publishes Docker image to GHCR
9. Publishes Helm chart to GHCR (OCI)
10. Deploys documentation to GitHub Pages

## Published artifacts

| Artifact     | Registry                                        |
|--------------|-------------------------------------------------|
| CLI (pip)    | [PyPI](https://pypi.org/p/shomer)               |
| Docker server | `ghcr.io/goabonga/shomer-server`               |
| Docker worker | `ghcr.io/goabonga/shomer-worker`               |
| Helm chart    | `oci://ghcr.io/goabonga/shomer-chart/shomer`   |
