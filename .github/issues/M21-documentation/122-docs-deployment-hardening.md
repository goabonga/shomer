# docs(deployment): production deployment and security hardening

## Description

Production deployment guide covering reverse proxy setup (Nginx/Caddy), TLS configuration, database hardening, secret management, monitoring, logging, and security checklist.

## Objective

Provide operators with a comprehensive guide to securely deploy Shomer in production.

## Tasks

- [ ] Reverse proxy configuration (Nginx with TLS termination)
- [ ] TLS/SSL best practices (ciphers, HSTS, certificate renewal)
- [ ] Database hardening (connection limits, SSL, backups)
- [ ] Redis security (authentication, TLS)
- [ ] Secret management (systemd-creds, HashiCorp Vault patterns)
- [ ] Logging configuration and log levels
- [ ] Monitoring and health checks (/healthz, /readyz)
- [ ] Rate limiting configuration
- [ ] Security headers checklist
- [ ] Production `.env` example with recommended settings
- [ ] Backup and disaster recovery

## Dependencies

- #2 — configuration module
- docs/install.md already covers basic installation

## Labels

`type:docs`, `type:infra`, `size:L`
