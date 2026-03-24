## docs(multitenancy): multi-tenancy and custom domains guide

## Summary

Guide for setting up and managing tenants: creation, member management, tenant resolution strategies, custom domains with SSL, and branding configuration.

## Changes

- [ ] Tenant creation and configuration
- [ ] Tenant resolution strategies (subdomain, path, custom domain)
- [ ] Custom domain setup: DNS CNAME, Nginx, SSL Certbot
- [ ] Branding configuration (logo, colors, CSS, favicon)
- [ ] Email template customization per tenant
- [ ] Member management and tenant roles (Owner, Admin, Member)
- [ ] Trust policies per tenant
- [ ] Tenant-scoped sessions and clients
- [ ] Deployment considerations for multi-tenant setups

## Dependencies

- #79–#83 - multi-tenancy implementation

## Related Issue

Closes #118

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present


