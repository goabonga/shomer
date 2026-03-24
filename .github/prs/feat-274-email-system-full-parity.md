## feat(email): align email system with auth/ — full parity

## Summary

Full email system parity with auth/: MJML compilation via mrml, plain text variants with BeautifulSoup fallback, 16-field branding palette, async renderer, per-tenant template overrides from DB, and global + tenant template caching.

## Changes

- [ ] Add `mrml` dependency and MJML-to-HTML compilation
- [ ] Convert HTML templates to MJML sources
- [ ] Add `.txt` plain text variants for all email types
- [ ] Auto-generate plain text from HTML via BeautifulSoup
- [ ] Send multipart emails (HTML + plain text)
- [ ] Extend branding to 16 fields (full semantic palette)
- [ ] Convert renderer and email service to async
- [ ] Add per-tenant template overrides from TenantTemplate model
- [ ] Add global + tenant template caching
- [ ] Unit tests for all new features

## Dependencies

- #10 - email service
- #82 - tenant branding
- #98 - MJML templates

## Related Issue

Closes #274

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present
