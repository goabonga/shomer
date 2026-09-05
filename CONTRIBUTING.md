# Contributing to Shomer

Thanks for taking the time to contribute. This document is the short
version of how to propose a change and what the project expects in return.

## Code of Conduct

Participation in this project is governed by the
[Code of Conduct](CODE_OF_CONDUCT.md). By contributing you agree to abide
by its terms.

## Development setup

The repository is a [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/).

```bash
git clone https://github.com/goabonga/shomer.git
cd shomer
uv sync
```

## Quality gates

```bash
uv run ruff check packages scripts
uv run ruff format --check packages scripts
```

## Commit messages

Commit messages MUST follow
[Conventional Commits](https://www.conventionalcommits.org/): a real type,
imperative mood, and a scope taken from the table below rather than
invented. A commit touching two scopes is split.

| Scope | Covers |
| --- | --- |
| `lib` | `packages/lib` |
| `bdd` | `packages/bdd` |
| `api` | `packages/api` |
| `cli` | `packages/cli` |
| `job` | `packages/job` |
| `web` | `packages/web` |
| `ssr` | `packages/ssr` |
| `chart-api`, `chart-bdd`, `chart-job`, `chart-ssr` | the matching `packages/*/chart` |
| `docs` | `docs/` and the site configuration |

A change to the pipeline, the governance files or the workspace root
carries no scope. It belongs to none of them, and inventing one would file
it under a component whose release it has nothing to do with.

Do not append `Co-Authored-By` trailers.

## Reporting bugs and asking for features

Please open a GitHub issue. For security-sensitive reports follow
[SECURITY.md](SECURITY.md) instead of the public tracker.
