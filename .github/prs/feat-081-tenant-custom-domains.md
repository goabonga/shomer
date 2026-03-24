## feat(tenant): custom domains (CNAME, Nginx, SSL Certbot)

## Summary

Custom domain support for tenants: CNAME verification, Nginx vhost configuration generation, SSL certificate provisioning via Certbot/Let's Encrypt.

## Changes

- [ ] CNAME/DNS verification service
- [ ] Nginx vhost config generation per tenant domain
- [ ] SSL certificate provisioning via Certbot
- [ ] Certificate renewal tracking
- [ ] Domain status tracking (pending_dns, pending_ssl, active, error)
- [ ] Admin API for domain management
- [ ] Integration tests (DNS verification)

## Dependencies

- #79 - Tenant model
- #80 - tenant resolver middleware

## Related Issue

Closes #81

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present


