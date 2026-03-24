## fix(bdd): harden flaky BDD tests with improved retry logic and email handling

## Summary

- Harden `register_and_verify_user()` and `get_latest_email()` with increased retries and exponential backoff
- Fix session cookie capture edge cases and add login retry logic for 401/403
- Improve Celery worker warmup to fully confirm responsiveness before running tests

## Changes

- [ ] Increase `get_latest_email()` retries from 20 to 30 with better logging
- [ ] Harden `register_and_verify_user()` with exponential backoff and HTTP status verification
- [ ] Improve Celery warmup in `environment.py` to fully confirm worker responsiveness
- [ ] Fix `_capture_session_cookie()` edge cases (quoted values, multiple Set-Cookie headers)
- [ ] Add retry logic on login step for 401/403 when email verification hasn't propagated yet
- [ ] Add small delay in auth_verify resend scenario to ensure rate limit window is hit

## Dependencies

- #237 — Previous flaky BDD fix attempt
- #251 — Email verification retry
- #252 — Login retry

## Related Issue

Closes #259

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass (target: 0 flaky failures)
- [ ] `make check-license` - SPDX headers present
