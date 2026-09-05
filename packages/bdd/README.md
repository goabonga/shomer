# shomer-bdd

[![PyPI](https://img.shields.io/pypi/v/shomer-bdd.svg)](https://pypi.org/project/shomer-bdd/)
[![Python](https://img.shields.io/pypi/pyversions/shomer-bdd.svg)](https://pypi.org/project/shomer-bdd/)
[![CI](https://github.com/goabonga/shomer/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/goabonga/shomer/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/goabonga/shomer/blob/main/LICENSE)

Database migrations for [Shomer](https://github.com/goabonga/shomer), an
OpenID Connect / OAuth 2.0 platform. It ships the Alembic revision tree
and the runner that applies it.

The model metadata it autogenerates against lives in
[`shomer-lib`](https://github.com/goabonga/shomer/tree/main/packages/lib),
and the revisions ship here rather than there so a service that only needs
the models never installs Alembic with them.

## Install

```bash
uv add shomer-bdd
# or
pip install 'shomer-bdd[postgres]'
```

## Usage

```bash
export SHOMER_DATABASE_URL="postgresql+psycopg://shomer@localhost/shomer"

shomer-bdd            # upgrade to head
shomer-bdd base       # or to any revision
```

The URL is resolved, never stored: `-x url=...` first, then
`sqlalchemy.url` from the ini, then `SHOMER_DATABASE_URL`. A checkout
carries no credentials and cannot be pointed at production by a file
somebody forgot to edit.

The runner only ever moves the schema to a revision. It does not create,
drop or seed a database — one that could is one nobody can safely hand
production credentials to.

## Authoring a revision

From a checkout of the
[repository](https://github.com/goabonga/shomer):

```bash
uv run alembic -c packages/bdd/alembic.ini revision --autogenerate -m "add x"
```

## Documentation

Project site: <https://goabonga.github.io/shomer/>.

## License

MIT — see [LICENSE](https://github.com/goabonga/shomer/blob/main/LICENSE).
