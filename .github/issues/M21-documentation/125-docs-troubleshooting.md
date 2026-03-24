# docs(troubleshooting): troubleshooting guide and FAQ

## Description

Common issues, error messages, and their solutions. FAQ section for frequently asked questions about deployment, configuration, and integration.

## Objective

Reduce support burden by documenting known issues and their resolutions.

## Tasks

- [ ] Common startup errors (database connection, missing secrets, migration issues)
- [ ] OAuth2 error troubleshooting (invalid_client, invalid_grant, invalid_redirect_uri)
- [ ] JWT validation errors (expired, invalid signature, wrong audience)
- [ ] Session issues (cookie not set, CSRF mismatch, cross-domain)
- [ ] Email delivery issues (SMTP connection, templates not rendering)
- [ ] MFA issues (TOTP clock drift, backup codes exhausted)
- [ ] Multi-tenancy issues (tenant not resolved, domain not verified)
- [ ] Performance tuning (database pool size, Celery concurrency)
- [ ] FAQ: general questions about Shomer capabilities and limitations

## Dependencies

None — can be updated continuously.

## Labels

`type:docs`, `size:M`
