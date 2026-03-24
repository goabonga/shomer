# feat(email): align email system with auth/ — full parity

## Description

The email system in Shomer is functional but lacks several features present in the auth/ project: MJML compilation via `mrml`, plain text email variants, full 16-field branding palette, async renderer, per-tenant template overrides from the database, and template caching. This issue brings the email subsystem to full parity.

## Objective

Achieve feature parity with auth/'s email system: MJML compilation, plain text fallback, complete branding palette, async rendering, tenant DB template overrides, and caching.

## Tasks

### MJML compilation
- [ ] Add `mrml` dependency (server extra)
- [ ] Implement MJML-to-HTML compilation in renderer (with `%var%` → `{{var}}` conversion)
- [ ] Convert existing HTML templates to MJML sources
- [ ] Keep compiled HTML as fallback when `mrml` is not available

### Plain text emails
- [ ] Add `.txt` template variants for all email types (verification, reset, MFA, welcome)
- [ ] Auto-generate plain text from HTML via BeautifulSoup fallback
- [ ] Send multipart emails (HTML + plain text) in SmtpBackend
- [ ] Add `beautifulsoup4` dependency (server extra)

### Full branding palette (16 fields)
- [ ] Extend branding context: add `accent_color`, `background_color`, `surface_color`, `text_color`, `text_muted_color`, `error_color`, `success_color`, `warning_color`, `info_color`, `border_color`, `font_family`
- [ ] Update base template to use all 16 branding fields
- [ ] Map TenantBranding model fields to renderer context

### Async renderer
- [ ] Convert `render_template()` to async
- [ ] Update `EmailService.send_email()` to async
- [ ] Ensure Celery task bridge works with async renderer

### Tenant template overrides
- [ ] Load per-tenant MJML/HTML overrides from `TenantTemplate` model
- [ ] Fall back to default templates when no override exists
- [ ] Add `render_email_for_tenant()` method

### Template caching
- [ ] Add global compiled template cache (MJML → HTML)
- [ ] Add tenant-specific template cache with invalidation
- [ ] Cache Jinja2 environments per template directory

### Tests
- [ ] Unit tests for MJML compilation
- [ ] Unit tests for plain text generation
- [ ] Unit tests for full branding palette injection
- [ ] Unit tests for tenant template overrides
- [ ] Unit tests for caching behavior

## Dependencies

- #10 — email service
- #82 — tenant branding
- #98 — MJML templates (current)

## Labels

`feature:email`, `priority:high`, `size:XL`
