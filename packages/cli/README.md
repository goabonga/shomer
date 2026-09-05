# shomer-cli

[![PyPI](https://img.shields.io/pypi/v/shomer-cli.svg)](https://pypi.org/project/shomer-cli/)
[![Python](https://img.shields.io/pypi/pyversions/shomer-cli.svg)](https://pypi.org/project/shomer-cli/)
[![CI](https://github.com/goabonga/shomer/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/goabonga/shomer/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/goabonga/shomer/blob/main/LICENSE)

Command-line interface of [Shomer](https://github.com/goabonga/shomer), an
OpenID Connect / OAuth 2.0 platform.

The commands read the same container the services run on — from
[`shomer-lib`](https://github.com/goabonga/shomer/tree/main/packages/lib) —
so `shomer config` reports what a service would actually resolve rather
than what a file claims.

## Install

```bash
uv add shomer-cli
# or
pip install shomer-cli
```

## Usage

```bash
shomer version      # what is installed
shomer config       # the settings this process actually resolved
shomer check-db     # can it reach the database it is configured for?
```

`shomer config` masks the database password, so its output is safe to
paste into an issue — which is what someone diagnosing a connection
problem does.

`shomer check-db` answers "can this process reach its database", which
is a different question from "has the schema been migrated". Conflating
the two makes a pre-migration instance look unreachable.

## Documentation

Project site: <https://goabonga.github.io/shomer/>.

## License

MIT — see [LICENSE](https://github.com/goabonga/shomer/blob/main/LICENSE).
