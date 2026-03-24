## docs(deployment): production deployment and security hardening

## Summary

Production deployment guide covering reverse proxy setup (Nginx/Caddy), TLS configuration, database hardening, secret management, monitoring, logging, and security checklist.

## Changes

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

- #2 - configuration module
- docs/install.md already covers basic installation

## Related Issue

Closes #122

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present


