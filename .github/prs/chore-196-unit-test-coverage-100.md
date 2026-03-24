## test(unit): achieve 100% unit test coverage

## Summary

Add missing unit tests to reach 100% line coverage on all source files.

## Changes

- [ ] routes/auth.py — cover register, verify, resend, login, logout, password reset/change
- [ ] routes/oauth2.py — cover consent rendering, client_credentials handler, password handler
- [ ] services/auth_service.py — cover change_password edge cases
- [ ] services/authorize_service.py — cover redirect_uri mismatch, response_type check, PKCE
- [ ] services/jwt_service.py — cover create_id_token
- [ ] services/jwt_validation_service.py — cover expired token path
- [ ] services/oauth2_client_service.py — cover auth method none, rotate_secret
- [ ] services/session_service.py — cover session cleanup
- [ ] services/token_service.py — cover TokenResponse.to_dict, PKCE plain
- [ ] deps.py — cover DB session error path
- [ ] middleware/session.py — cover session refresh path
- [ ] models/queries.py — cover get_user_by_id
- [ ] models/user.py, user_email.py, user_password.py — cover __repr__
- [ ] tasks/email.py — cover send_email task

## Related Issue

Closes #196

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass with 100% coverage
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present
