# Shomer

OIDC/OAuth2 authentication service.

## Distribution

Shomer is available as:

- **PyPI** via [PyPI](https://pypi.org/p/shomer)
    - `pip install shomer` - CLI only
    - `pip install shomer[server]` - CLI + web server
    - `pip install shomer[worker]` - CLI + Celery worker
    - `pip install shomer[server,worker]` - all components
- **Docker images** via GHCR
    - [`ghcr.io/goabonga/shomer-server`](https://ghcr.io/goabonga/shomer-server) - API server
    - [`ghcr.io/goabonga/shomer-worker`](https://ghcr.io/goabonga/shomer-worker) - Celery worker / beat
- **Helm chart** via [GHCR OCI](https://ghcr.io/goabonga/shomer-chart) for Kubernetes deployments

See the [Installation](install.md) page for details.
