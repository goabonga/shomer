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

The repository is a [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/)
alongside an npm workspace.
Every package is versioned, changelogged, tagged and released on its own.

| Package | Kind | What it is |
| --- | --- | --- |
| [`shomer-lib`](packages/lib) | Python | Contracts, settings, ORM models, database connector, DI module. |
| [`shomer-bdd`](packages/bdd) | Python | The Alembic revisions and their runner. |
| [`shomer-api`](packages/api) | Python | The OpenID Connect / OAuth 2.0 endpoints. |
| [`shomer-cli`](packages/cli) | Python | The operator command line. |
| [`shomer-job`](packages/job) | Python | The maintenance worker. |
| [`shomer-web`](packages/web) | TypeScript | The React sources the frontend serves. |

`shomer-web` builds into the frontend's `static/` and `templates/`
directories, so a frontend change ships in the next release of it — the
dependency is declared to the release tooling rather than left to whoever
remembers it.
| [`shomer-ssr`](packages/ssr) | Python | The server-side rendered frontend. |

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

## What gets published

| Package | PyPI | Image | Chart |
| --- | :---: | :---: | :---: |
| `shomer-lib` | ✅ | | |
| `shomer-bdd` | ✅ | ✅ | ✅ |
| `shomer-api` | ✅ | ✅ | ✅ |
| `shomer-cli` | ✅ | | |
| `shomer-job` | ✅ | ✅ | ✅ |
| `shomer-ssr` | ✅ | ✅ | ✅ |
| `shomer-web` | | | |

Images go to `ghcr.io/goabonga/shomer-<name>`, charts to
`oci://ghcr.io/goabonga/charts`. Both are signed keylessly with cosign
and verified in the same job that pushes them; images additionally carry
their SBOM as an SPDX attestation.

```bash
helm install api oci://ghcr.io/goabonga/charts/shomer-api \
  --set settings.issuer=https://id.example.com \
  --set settings.existingSecret=shomer-db
```

Each chart can also make the cluster check the signature rather than
trusting that CI did. It is off by default — the object means nothing
unless the matching admission controller is installed, and a chart that
assumes one fails in ways nobody can read.

```bash
  --set imageVerification.enabled=true \
  --set imageVerification.validationFailureAction=Enforce
```

CI proves that policy is not inert: it installs Kyverno in a throwaway
cluster, turns the policy on in Enforce, and asserts that an image the
policy matches but whose signature carries someone else's identity is
rejected — then admitted once the policy is removed, so the rejection
cannot have come from anything else.

Network rules ship as `networking.k8s.io/v1` by default, since Calico and
Cilium both implement it. Switch to their own kinds when a rule needs
something the upstream API cannot say — an explicit `Deny` and ordering
for Calico, DNS names and L7 for Cilium:

```bash
  --set networkPolicy.provider=cilium
```

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
- Node **22+** (for the TypeScript packages)

## Getting started

```bash
git clone https://github.com/goabonga/shomer.git
cd shomer

uv sync --all-packages
npm ci

npm run build --workspace packages/web   # bundle the frontend into the ssr package

uv run shomer-bdd                        # apply the migrations
uv run shomer-api                        # http://localhost:8000
uv run shomer-ssr                        # http://localhost:8080
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
