# Contributing to Shomer

Thanks for taking the time to contribute. This document is the short
version of how to propose a change and what the project expects in return.

## Code of Conduct

Participation in this project is governed by the
[Code of Conduct](CODE_OF_CONDUCT.md). By contributing you agree to abide
by its terms.

## Development setup

The repository is a [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/)
for the Python packages and an npm workspace for the TypeScript ones.
Both live side by side and are installed separately.

```bash
git clone https://github.com/goabonga/shomer.git
cd shomer

uv sync --all-packages          # Python packages + dev tooling
npm ci                          # TypeScript packages (hoisted at the root)
uv run pre-commit install       # pre-commit + commit-msg hooks
```

## Quality gates

Before pushing, run the same gates the `ci` workflow runs.

```bash
# Python (packages/ssr)
uv run ruff check packages/ssr
uv run ruff format --check packages/ssr
uv run mypy --strict packages/ssr/src
uv run pytest packages/ssr/tests

# TypeScript (packages/web)
npm run lint --workspace packages/web
npm run format:check --workspace packages/web
npm run typecheck --workspace packages/web
npm run test --workspace packages/web

# Repository-wide
uv tool run multicz validate --strict
uv run python scripts/add_license_header.py --path packages --check
uv run python scripts/add_license_header.py --path scripts --types py,sh --check
```

`packages/web` builds into `packages/ssr/src/shomer_ssr/{static,templates}/`.
Never edit those two directories by hand — edit the sources under
`packages/web/src/` and run `npm run build --workspace packages/web`.

## Commit messages

Commit messages MUST follow
[Conventional Commits](https://www.conventionalcommits.org/). They drive
the version bump and the CHANGELOG computed by
[multicz](https://github.com/goabonga/multicz), per component.

| Type | Effect on version | Use it for |
| --- | --- | --- |
| `feat` | minor | new capability |
| `fix` | patch | bug fix |
| `perf` | patch | performance improvement |
| `refactor`, `docs`, `test`, `chore`, `ci`, `build`, `style` | none | maintenance |
| `feat!` / `BREAKING CHANGE:` | major | incompatible change |

Which component a commit releases is decided by the paths it touches, not
by the scope you write — see `paths` in [multicz.toml](multicz.toml). Do
not append `Co-Authored-By` trailers.

## Releasing

Releases are automated. On every push to `main` the `ci` workflow runs
`multicz bump` (signed commit, one tag per bumped component) and the
`release-<component>` jobs publish what changed. Maintainers do not bump
versions or edit changelogs by hand.

## Reporting bugs and asking for features

Please open a GitHub issue. For security-sensitive reports follow
[SECURITY.md](SECURITY.md) instead of the public tracker.
