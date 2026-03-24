## feat(tenant): branding - TenantBranding + TenantTemplate + rendering

## Summary

Tenant branding support: TenantBranding (logo, colors, favicon), TenantTemplate (custom email/page templates), and rendering engine that applies branding to all UI pages and emails.

## Changes

- [ ] TenantBranding model (logo_url, primary_color, secondary_color, favicon_url, custom_css)
- [ ] TenantTemplate model (tenant_id, template_type, template_content)
- [ ] Branding resolution in template rendering
- [ ] Apply branding to login, consent, error pages
- [ ] Apply branding to email templates
- [ ] Alembic migration

## Dependencies

- #79 - Tenant model

## Related Issue

Closes #82

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present


