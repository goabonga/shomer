# shomer-api

[![PyPI](https://img.shields.io/pypi/v/shomer-api.svg)](https://pypi.org/project/shomer-api/)
[![Python](https://img.shields.io/pypi/pyversions/shomer-api.svg)](https://pypi.org/project/shomer-api/)
[![CI](https://github.com/goabonga/shomer/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/goabonga/shomer/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/goabonga/shomer/blob/main/LICENSE)

Authorization API of [Shomer](https://github.com/goabonga/shomer), an
OpenID Connect / OAuth 2.0 platform.

Endpoints are resolved through the shared container from
[`shomer-lib`](https://github.com/goabonga/shomer/tree/main/packages/lib),
so a handler names the interface it needs and never the implementation
behind it.

## Install

```bash
uv add shomer-api
# or
pip install shomer-api
```

## Usage

```bash
export SHOMER_ISSUER="https://id.example.com"
export SHOMER_DATABASE_URL="postgresql+psycopg://shomer@localhost/shomer"

shomer-api            # listens on 0.0.0.0:8000
```

Apply the schema first with
[`shomer-bdd`](https://github.com/goabonga/shomer/tree/main/packages/bdd).

## Endpoints

| Endpoint | What it does |
| --- | --- |
| `GET /healthz` | Liveness. Reads the clock through the container, so a process that can no longer resolve its dependencies fails the probe. |
| `GET /.well-known/openid-configuration` | The discovery document, every URL derived from the configured issuer. |

## Status

The OAuth 2.0 grants are **not implemented yet**. Discovery advertises
only what exists — listing a grant the server does not serve sends clients
down a path ending in a 404 they cannot interpret.

## Documentation

Project site: <https://goabonga.github.io/shomer/>.

## License

MIT — see [LICENSE](https://github.com/goabonga/shomer/blob/main/LICENSE).
