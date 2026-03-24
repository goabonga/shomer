## feat(email): MJML templates (verification, reset, MFA, welcome)

## Summary

Production-ready MJML email templates for: email verification, password reset, MFA code, welcome email. Support for tenant branding (logo, colors).

## Changes

- [ ] MJML base layout with branding slots
- [ ] Email verification template (code display)
- [ ] Password reset template (reset link/code)
- [ ] MFA email fallback template (6-digit code)
- [ ] Welcome email template
- [ ] Tenant branding integration (logo, colors, footer)
- [ ] Compile MJML to HTML
- [ ] Preview/test tooling

## Dependencies

- #10 - email service
- #82 - tenant branding

## Related Issue

Closes #98

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present


