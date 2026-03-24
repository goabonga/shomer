## feat(email): email sending service (SMTP/Mailler) via Celery

## Summary

Async email sending service with SMTP and Mailler as backends, dispatched via Celery tasks. Jinja2 templates for HTML rendering.

## Changes

- [ ] Email service interface (send_email with subject, to, template, context)
- [ ] SMTP backend implementation
- [ ] Mailler backend implementation
- [ ] Celery task wrapper for async dispatch
- [ ] Jinja2 template rendering engine
- [ ] Unit tests with mock SMTP server
- [ ] Retry policy for transient failures

## Dependencies

- #2 - configuration

## Related Issue

Closes #10

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present


