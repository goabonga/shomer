# shomer-job

[![PyPI](https://img.shields.io/pypi/v/shomer-job.svg)](https://pypi.org/project/shomer-job/)
[![Python](https://img.shields.io/pypi/pyversions/shomer-job.svg)](https://pypi.org/project/shomer-job/)
[![CI](https://github.com/goabonga/shomer/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/goabonga/shomer/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/goabonga/shomer/blob/main/LICENSE)

Background worker of [Shomer](https://github.com/goabonga/shomer), an
OpenID Connect / OAuth 2.0 platform.

An authorization server accumulates state that expires on a clock rather
than on a request — authorization codes, sessions, refresh tokens. This is
the process that clears it. Sweeping from the request path would charge
the cost to whichever user arrived at the wrong moment, and would never
run at all while the service is idle.

## Install

```bash
uv add shomer-job
# or
pip install shomer-job
```

## Usage

```bash
shomer-job                 # run one tick and exit
shomer-job --loop          # run continuously
shomer-job --interval 30
```

One tick and exit is the default because it is the shape a scheduler — a
cron entry, a Kubernetes `Job` — can supervise: a run either succeeds or
fails, and a failure is visible without reading a long-lived process's
logs.

It is wired from
[`shomer-lib`](https://github.com/goabonga/shomer/tree/main/packages/lib)
like every other service.

## Documentation

Project site: <https://goabonga.github.io/shomer/>.

## License

MIT — see [LICENSE](https://github.com/goabonga/shomer/blob/main/LICENSE).
