## fix(ui): integrate MFA status and PAT link in security settings page

## Summary

Update security settings page to show real MFA status (enabled/disabled), link to setup/disable, and add Tokens link to all settings nav pages.

## Changes

### MFA integration

- [ ] Query UserMFA status for authenticated user
- [ ] Display enabled/disabled with methods
- [ ] Link to /ui/mfa/setup or disable button
- [ ] Backup codes regeneration link

### Settings navigation

- [ ] Add Tokens link to all 4 settings pages (profile, emails, security, pats)
- [ ] Consistent nav across pages

### Tests

- [ ] Updated unit tests
- [ ] BDD happy path

## Dependencies

- #66 - MFA setup API
- #70 - MFA UI
- #78 - PAT UI

## Related Issue

Closes #245

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present
