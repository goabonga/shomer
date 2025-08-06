# Shomer

OIDC/OAuth2 authentication service.

## Installation

### CLI only

```bash
pip install shomer
```

### CLI + Server

```bash
pip install shomer[server]
```

### CLI + Worker

```bash
pip install shomer[worker]
```

### All components

```bash
pip install shomer[server,worker]
```

### Docker

```bash
docker pull ghcr.io/goabonga/shomer-server:latest
docker run -p 8000:8000 ghcr.io/goabonga/shomer-server:latest
```

### Docker Compose

```bash
git clone https://github.com/goabonga/shomer.git
cd shomer
make docker-up
```

### Helm

```bash
helm install shomer oci://ghcr.io/goabonga/shomer-chart/shomer --version 0.0.0
```

## Development

See [CONTRIBUTING.md](https://github.com/goabonga/shomer/blob/main/CONTRIBUTING.md) for the full contribution guide.

## License

[MIT](https://github.com/goabonga/shomer/blob/main/LICENSE)
