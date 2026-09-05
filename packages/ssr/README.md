# shomer-ssr

[![PyPI](https://img.shields.io/pypi/v/shomer-ssr.svg)](https://pypi.org/project/shomer-ssr/)
[![Python](https://img.shields.io/pypi/pyversions/shomer-ssr.svg)](https://pypi.org/project/shomer-ssr/)
[![CI](https://github.com/goabonga/shomer/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/goabonga/shomer/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/goabonga/shomer/blob/main/LICENSE)

Server-side rendered frontend of
[Shomer](https://github.com/goabonga/shomer), an OpenID Connect /
OAuth 2.0 platform.

It serves one shell for every route, injects the runtime configuration the
browser needs, and lets the React app render the rest.

## Install

```bash
uv add shomer-ssr
# or
pip install shomer-ssr
```

## Usage

```bash
export SHOMER_ISSUER="https://id.example.com"

shomer-ssr            # listens on 0.0.0.0:8080
```

The issuer reaches the browser through the injected settings rather than a
constant compiled into the bundle: the browser has to send the user to the
same origin the tokens will claim to come from, and two copies of that
value drift the first time one deployment is reconfigured.

## Assets

`static/` and `templates/` are build outputs of
[`packages/web`](https://github.com/goabonga/shomer/tree/main/packages/web).
Edit the sources there, never the copies shipped in this wheel.

## Documentation

Project site: <https://goabonga.github.io/shomer/>.

## License

MIT — see [LICENSE](https://github.com/goabonga/shomer/blob/main/LICENSE).
