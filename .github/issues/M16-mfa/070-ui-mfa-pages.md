# feat(mfa): [UI] TOTP setup, MFA challenge, and email fallback pages

## Description

Jinja2/HTMX pages: MFA setup (QR code display, verification code input, backup codes display), MFA challenge (TOTP code input during login), email fallback (send code button, code input).

## Objective

Provide the browser UI for all MFA interactions.

## Tasks

- [ ] MFA setup page: QR code, manual secret, verification code input
- [ ] Backup codes display page (after setup)
- [ ] MFA challenge page during login (TOTP code input)
- [ ] Email fallback option: "Send code by email" button
- [ ] Email code input page
- [ ] Backup code input option

## Dependencies

- #66 — MFA setup API
- #67 — MFA verify API
- #68 — MFA login challenge

## Labels

`feature:mfa`, `feature:auth`, `layer:ui`, `size:L`
