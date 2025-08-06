# Installation

## PyPI

- `pip install shomer` - CLI only
- `pip install shomer[server]` - CLI + web server (FastAPI, uvicorn, Jinja2)
- `pip install shomer[worker]` - CLI + Celery worker
- `pip install shomer[server,worker]` - all components - see [Systemd](#systemd) for a production setup

```bash
shomer --version
```

## Docker

Pull and run the pre-built image from GitHub Container Registry:

```bash
docker pull ghcr.io/goabonga/shomer-server:{{ version }}
docker run -p 8000:8000 ghcr.io/goabonga/shomer-server:{{ version }}
```

The app will be available at [http://localhost:8000](http://localhost:8000).

### Environment variables

| Variable | Default   | Description        |
|----------|-----------|--------------------|
| `HOST`   | `0.0.0.0` | Server bind address |
| `PORT`   | `8000`    | Server port         |

```bash
docker run -p 9000:9000 -e PORT=9000 ghcr.io/goabonga/shomer-server:{{ version }}
```

## Docker Compose

```bash
git clone https://github.com/goabonga/shomer.git
cd shomer
make docker-up
```

To stop the service:

```bash
make docker-down
```

## Helm

Deploy to a Kubernetes cluster using the OCI Helm chart from GHCR:

```bash
helm install shomer oci://ghcr.io/goabonga/shomer-chart/shomer --version {{ version }}
```

### Custom values

```bash
helm install shomer oci://ghcr.io/goabonga/shomer-chart/shomer \
  --version {{ version }} \
  --set replicaCount=3 \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host=shomer.example.com \
  --set ingress.hosts[0].paths[0].path=/ \
  --set ingress.hosts[0].paths[0].pathType=Prefix
```

## Systemd

Run Shomer as a systemd service on a Linux server.

### Create a dedicated user

```bash
sudo useradd --system --no-create-home --shell /usr/sbin/nologin shomer
```

### Install the application

```bash
sudo python3 -m venv /opt/shomer
sudo /opt/shomer/bin/pip install shomer[server,worker]
```

### Create the service units

#### API server

```bash
sudo tee /etc/systemd/system/shomer.service > /dev/null << 'EOF'
[Unit]
Description=Shomer API server
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=shomer
Group=shomer
WorkingDirectory=/opt/shomer
Environment=SHOMER_DATABASE_URL=postgresql+asyncpg://shomer:shomer@localhost:5432/shomer
Environment=SHOMER_CELERY_BROKER_URL=redis://localhost:6379/0
ExecStart=/opt/shomer/bin/uvicorn shomer.app:app --host 127.0.0.1 --port 8000
Restart=on-failure
RestartSec=5

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
PrivateDevices=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictSUIDSGID=true
RestrictNamespaces=true
RestrictRealtime=true
MemoryDenyWriteExecute=true
LockPersonality=true
SystemCallArchitectures=native

[Install]
WantedBy=multi-user.target
EOF
```

#### Celery worker

```bash
sudo tee /etc/systemd/system/shomer-worker.service > /dev/null << 'EOF'
[Unit]
Description=Shomer Celery worker
After=network.target redis.service

[Service]
Type=exec
User=shomer
Group=shomer
WorkingDirectory=/opt/shomer
Environment=PYTHONPATH=/opt/shomer/lib/python3.13/site-packages
Environment=SHOMER_DATABASE_URL=postgresql+asyncpg://shomer:shomer@localhost:5432/shomer
Environment=SHOMER_CELERY_BROKER_URL=redis://localhost:6379/0
ExecStart=/opt/shomer/bin/celery -A shomer.worker worker --loglevel=info
Restart=on-failure
RestartSec=5

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
PrivateDevices=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictSUIDSGID=true
RestrictNamespaces=true
RestrictRealtime=true
MemoryDenyWriteExecute=true
LockPersonality=true
SystemCallArchitectures=native

[Install]
WantedBy=multi-user.target
EOF
```

#### Celery beat

```bash
sudo tee /etc/systemd/system/shomer-beat.service > /dev/null << 'EOF'
[Unit]
Description=Shomer Celery beat scheduler
After=network.target redis.service

[Service]
Type=exec
User=shomer
Group=shomer
WorkingDirectory=/opt/shomer
Environment=PYTHONPATH=/opt/shomer/lib/python3.13/site-packages
Environment=SHOMER_DATABASE_URL=postgresql+asyncpg://shomer:shomer@localhost:5432/shomer
Environment=SHOMER_CELERY_BROKER_URL=redis://localhost:6379/0
ExecStart=/opt/shomer/bin/celery -A shomer.worker beat --loglevel=info
Restart=on-failure
RestartSec=5

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
PrivateDevices=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictSUIDSGID=true
RestrictNamespaces=true
RestrictRealtime=true
MemoryDenyWriteExecute=true
LockPersonality=true
SystemCallArchitectures=native

[Install]
WantedBy=multi-user.target
EOF
```

### Enable and start

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now shomer shomer-worker shomer-beat
sudo systemctl status shomer shomer-worker shomer-beat
```