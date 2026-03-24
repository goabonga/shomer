# feat(tenant): branding — TenantBranding + TenantTemplate + rendering

## Description

Tenant branding support: TenantBranding (logo, colors, favicon), TenantTemplate (custom email/page templates), and rendering engine that applies branding to all UI pages and emails.

## Objective

Allow each tenant to customize the look and feel of auth pages and emails.

## Tasks

- [ ] TenantBranding model (logo_url, primary_color, secondary_color, favicon_url, custom_css)
- [ ] TenantTemplate model (tenant_id, template_type, template_content)
- [ ] Branding resolution in template rendering
- [ ] Apply branding to login, consent, error pages
- [ ] Apply branding to email templates
- [ ] Alembic migration

## Dependencies

- #79 — Tenant model

## Labels

`feature:tenant`, `size:L`
