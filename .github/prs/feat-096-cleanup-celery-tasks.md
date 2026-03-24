## feat(cleanup): Celery Beat cleanup tasks for expired data

## Summary

Scheduled Celery Beat tasks for cleaning up expired data: expired tokens (access + refresh), expired authorization codes, expired device codes, expired PAR requests, expired verification codes, expired sessions, expired MFA codes, expired PATs.

## Changes

- [ ] Task: clean expired AccessTokens
- [ ] Task: clean expired RefreshTokens
- [ ] Task: clean expired AuthorizationCodes
- [ ] Task: clean expired DeviceCodes
- [ ] Task: clean expired PARRequests
- [ ] Task: clean expired VerificationCodes and PasswordResetTokens
- [ ] Task: clean expired Sessions
- [ ] Task: clean expired MFA codes
- [ ] Task: clean expired PATs
- [ ] Celery Beat schedule configuration
- [ ] Batch deletion with configurable batch size
- [ ] Logging and metrics

## Dependencies

- #16 - token models
- #29 - AuthorizationCode
- #52 - DeviceCode
- #57 - PARRequest
- #7 - VerificationCode
- #6 - Session
- #64 - MFA models
- #74 - PAT model

## Related Issue

Closes #96

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present


