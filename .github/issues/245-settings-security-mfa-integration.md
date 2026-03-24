# fix(ui): integrate MFA status and PAT link in security settings page

## Description

The security settings page (`/ui/settings/security`) still shows "MFA is not yet available." despite MFA being fully implemented (issues #64-#70). The settings nav also doesn't include the Tokens link added in #78. This issue updates the security page to show real MFA status and link to setup/disable, and ensures consistent navigation across all settings pages.

## Objective

Make the security settings page reflect the actual MFA state and provide a complete settings navigation.

## Tasks

### MFA integration

- [ ] Query UserMFA for the authenticated user
- [ ] Display MFA status (enabled/disabled) with methods list
- [ ] Link to `/ui/mfa/setup` when MFA is disabled
- [ ] "Disable MFA" button when MFA is enabled (requires TOTP verification)
- [ ] Show backup codes regeneration link when MFA is enabled

### Settings navigation

- [ ] Add "Tokens" link to settings nav on security page
- [ ] Add "Tokens" link to settings nav on profile page
- [ ] Add "Tokens" link to settings nav on emails page
- [ ] Ensure consistent nav across all 4 settings pages (Profile, Emails, Security, Tokens)

### Tests

- [ ] Update unit tests for security settings page
- [ ] BDD happy path: security page shows MFA status

## Dependencies

- #66 — MFA setup API
- #70 — MFA UI pages
- #78 — PAT management UI

## Labels

`bug`, `priority:high`, `layer:ui`, `size:S`
