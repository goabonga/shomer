<div align="center">
  <img src="assets/shomer.svg" alt="Shomer" width="120" />

  <h1>Shomer</h1>

  <p><strong>Shomer</strong> (<em>שׁוֹמֵר</em>) is Hebrew for <em>guardian</em>,
  <em>watchman</em> — the one who keeps watch over the gate.</p>

  <p>Shomer is an <strong>OpenID Connect / OAuth 2.0</strong> platform.</p>

  [![ci](https://github.com/goabonga/shomer/actions/workflows/ci.yml/badge.svg)](https://github.com/goabonga/shomer/actions/workflows/ci.yml)
  [![docs](https://img.shields.io/badge/docs-github.io-blue)](https://goabonga.github.io/shomer/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
  [![Python](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/)
  [![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
</div>

---

## Documentation

The full documentation is published at
**[goabonga.github.io/shomer](https://goabonga.github.io/shomer/)**.

## Packages

The repository is a [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/). Every package is versioned, changelogged,
tagged and released on its own.

| Package | Kind | What it is |
| --- | --- | --- |
| [`shomer-lib`](packages/lib) | Python | Contracts, settings, ORM models, database connector, DI module. |
| [`shomer-bdd`](packages/bdd) | Python | The Alembic revisions and their runner. |
| [`shomer-api`](packages/api) | Python | The OpenID Connect / OAuth 2.0 endpoints. |
| [`shomer-cli`](packages/cli) | Python | The operator command line. |
| [`shomer-job`](packages/job) | Python | The maintenance worker. |

`shomer-lib` sits at the root: every service names an interface it
declares and lets the container supply the implementation, so a service
never mentions a concrete class and swapping one is a change in a single
place.

## Dependency injection

Wiring goes through [tripack](https://github.com/goabonga/tripack), the
typed IoC container. `shomer_lib.module.ShomerModule` is the one place
that decides which implementation answers which contract; services
install it and ask for what they need.

```python
from shomer_lib.contracts import Settings
from shomer_lib.module import build_container

with build_container() as container:
    print(container.resolve(Settings).issuer)
```

In the two FastAPI services the container is owned by `TripackAPI`, so a
handler declares its dependency in the signature:

```python
@app.get("/healthz")
def healthz(clock: Annotated[Clock, Inject]) -> dict[str, object]:
    return {"status": "ok", "time": clock.now()}
```

## Requirements

- Python **3.13+**
- [uv](https://docs.astral.sh/uv/)

## Getting started

```bash
git clone https://github.com/goabonga/shomer.git
cd shomer

uv sync --all-packages

uv run shomer-bdd                        # apply the migrations
uv run shomer-api                        # http://localhost:8000
uv run shomer config                     # what this environment resolves to
```

With nothing configured it runs against a local SQLite file. Point it
elsewhere with `SHOMER_DATABASE_URL` and `SHOMER_ISSUER`.

## Versioning and releases

Versions are not edited by hand. [multicz](https://github.com/goabonga/multicz)
reads the [Conventional Commits](https://www.conventionalcommits.org/) since
each component's last tag, decides the bump, writes the changelog and tags
the release. On every push to `main`, CI bumps everything that changed in
one commit and publishes each component from its own job.

Which component a commit releases is decided by the paths it touches — see
`paths` in [multicz.toml](multicz.toml).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Security reports go through
[SECURITY.md](SECURITY.md), not the public tracker.

## License

[MIT](LICENSE) © 2026 Chris
