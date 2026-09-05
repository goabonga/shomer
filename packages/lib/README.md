# shomer-lib

[![PyPI](https://img.shields.io/pypi/v/shomer-lib.svg)](https://pypi.org/project/shomer-lib/)
[![Python](https://img.shields.io/pypi/pyversions/shomer-lib.svg)](https://pypi.org/project/shomer-lib/)
[![CI](https://github.com/goabonga/shomer/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/goabonga/shomer/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/goabonga/shomer/blob/main/LICENSE)

Shared library of [Shomer](https://github.com/goabonga/shomer), an
OpenID Connect / OAuth 2.0 platform. It holds what every service needs and
none of them should redefine: the contracts they type against, the
settings they read, the ORM models, the database connector, and the
dependency-injection module that binds the three together.

Every other package in the platform is wired from this one —
[`shomer-api`](https://github.com/goabonga/shomer/tree/main/packages/api),
[`shomer-cli`](https://github.com/goabonga/shomer/tree/main/packages/cli),
[`shomer-job`](https://github.com/goabonga/shomer/tree/main/packages/job),
[`shomer-ssr`](https://github.com/goabonga/shomer/tree/main/packages/ssr) —
and the migrations in
[`shomer-bdd`](https://github.com/goabonga/shomer/tree/main/packages/bdd)
autogenerate against the models declared here.

## Install

```bash
uv add shomer-lib
# or
pip install shomer-lib
```

Database drivers are extras; install the one you connect to. SQLite needs
none, which is why a first run needs nothing installed.

```bash
pip install 'shomer-lib[postgres]'
pip install 'shomer-lib[mysql]'
```

## Usage

A service names an interface and lets the container supply the
implementation. It never mentions `EnvSettings`, `SystemClock` or
`SqlAlchemyDatabase` — swapping one of those is an edit in
`ShomerModule` and nowhere else.

```python
from shomer_lib.contracts import Clock, Database, Settings
from shomer_lib.module import build_container

with build_container() as container:
    settings = container.resolve(Settings)
    print(settings.issuer)
```

The `with` block is not decoration: closing the container is what
disposes the connection pool.

## Configuration

| Variable | Default | What it is |
| --- | --- | --- |
| `SHOMER_ISSUER` | `http://localhost:8000` | The `iss` claim, and the base of the discovery URLs. |
| `SHOMER_DATABASE_URL` | `sqlite+pysqlite:///./shomer.db` | SQLAlchemy URL of the backing database. |

## Documentation

Project site: <https://goabonga.github.io/shomer/>.

## License

MIT — see [LICENSE](https://github.com/goabonga/shomer/blob/main/LICENSE).
