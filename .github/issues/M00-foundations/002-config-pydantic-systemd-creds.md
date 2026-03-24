# feat(config): Pydantic settings with file-based secrets support

## Description

Centralized configuration model using Pydantic BaseSettings. Supports environment variables, `.env` files, and file-based secrets from any provider (systemd-creds, HashiCorp Vault Agent, Kubernetes Secrets, CSI volumes).

Secrets are read from a configurable directory (`SHOMER_SECRETS_DIR`), defaulting to `/run/credentials` (systemd-creds convention). This is provider-agnostic: Vault Agent writes to `/vault/secrets/`, K8s mounts to `/run/secrets/`, systemd-creds uses `/run/credentials/` — the app doesn't care which one, it just reads files from the configured path.

## Objective

Ensure the application fails fast on misconfiguration and provides a single source of truth for all settings, with secrets loaded from files regardless of the secret management backend.

## Tasks

- [x] Pydantic BaseSettings with split connection components (db host/port/user/password/name, redis host/port/db/password)
- [x] `get_credential()` reads secrets from `CREDENTIALS_DIRECTORY` (systemd-creds, Vault, K8s) with env var fallback
- [x] Priority chain: env vars > secret files > .env file > defaults
- [x] `.env` file loading with environment-based overrides
- [x] Unit tests for settings, get_credential, and priority chain
- [x] Docker Compose: use Docker secrets for database and redis passwords
- [x] Helm chart: K8s Secret for passwords, volume mount at `/run/credentials`, `enableServiceLinks: false`
- [ ] Validation rules (URL formats, key lengths, required secrets)

## Deployment examples

### systemd-creds

```bash
systemd-creds encrypt master-key.txt /etc/credstore/shomer_master_key
# systemd decrypts to /run/credentials/shomer_master_key at runtime
```

### Vault Agent (Kubernetes)

```yaml
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/agent-inject-secret-database_url: "secret/shomer/database_url"
  vault.hashicorp.com/agent-inject-template-database_url: |
    {{- with secret "secret/shomer/database_url" -}}{{ .Data.data.value }}{{- end -}}
# Vault Agent writes to /vault/secrets/database_url
# Set SHOMER_SECRETS_DIR=/vault/secrets
```

### Kubernetes Secrets (volume mount)

```yaml
volumes:
  - name: shomer-secrets
    secret:
      secretName: shomer-config
volumeMounts:
  - name: shomer-secrets
    mountPath: /run/secrets
    readOnly: true
# Set SHOMER_SECRETS_DIR=/run/secrets
```

### Vault CSI Provider

```yaml
volumes:
  - name: secrets
    csi:
      driver: secrets-store.csi.k8s.io
      readOnly: true
      volumeAttributes:
        secretProviderClass: shomer-vault
volumeMounts:
  - name: secrets
    mountPath: /mnt/secrets
    readOnly: true
# Set SHOMER_SECRETS_DIR=/mnt/secrets
```

## Dependencies

None.

## Labels

`type:infra`, `size:M`
