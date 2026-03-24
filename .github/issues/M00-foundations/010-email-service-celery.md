# feat(email): email sending service (SMTP/Mailler) via Celery

## Description

Async email sending service with SMTP and Mailler as backends, dispatched via Celery tasks. Jinja2 templates for HTML rendering.

## Objective

Provide a reliable, async email sending pipeline that all features (verification, reset, MFA, welcome) can use.

## Tasks

- [ ] Email service interface (send_email with subject, to, template, context)
- [ ] SMTP backend implementation
- [ ] Mailler backend implementation
- [ ] Celery task wrapper for async dispatch
- [ ] Jinja2 template rendering engine
- [ ] Unit tests with mock SMTP server
- [ ] Retry policy for transient failures

## Dependencies

- #2 — configuration

## Labels

`feature:email`, `type:service`, `size:L`
