# fix(bdd): harden flaky BDD tests with improved retry logic and email handling

## Description

~31 BDD scenarios fail intermittently due to Celery worker email delivery delays, session cookie parsing edge cases, and insufficient retry logic. Most failures cascade from `register_and_verify_user()` timing out on email retrieval, causing all dependent tests (MFA, OAuth2, PAT, profile, userinfo) to fail.

## Objective

Make all BDD tests reliable by improving retry logic, email handling, and session cookie capture.

## Tasks

### Email and registration robustness

- [ ] Increase `get_latest_email()` retries from 20 to 30 with better logging
- [ ] Harden `register_and_verify_user()` with exponential backoff and HTTP status verification
- [ ] Improve Celery warmup in `environment.py` to fully confirm worker responsiveness

### Session and auth handling

- [ ] Fix `_capture_session_cookie()` edge cases (quoted values, multiple Set-Cookie headers)
- [ ] Add retry logic on login step for 401/403 when email verification hasn't propagated yet

### Rate limit timing

- [ ] Add small delay in auth_verify resend scenario to ensure rate limit window is hit

## Dependencies

- #237 — Previous flaky BDD fix attempt
- #251 — Email verification retry
- #252 — Login retry

## Labels

`bug`, `priority:high`, `layer:test`, `size:M`
