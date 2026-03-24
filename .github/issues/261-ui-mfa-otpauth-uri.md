# feat(ui): display otpauth: provisioning URI on MFA setup page

## Description

The MFA setup page (`/ui/mfa/setup`) shows the QR code and a manual secret entry, but does not display the full `otpauth://` provisioning URI. Users who want to copy-paste the URI directly into their authenticator app (or use a CLI-based TOTP tool) have no way to do so.

## Objective

Display the `otpauth://totp/...` provisioning URI on the MFA setup page so users can copy it directly.

## Tasks

- [ ] Add otpauth: URI display in a copyable field on the MFA setup template
- [ ] Unit test for provisioning URI in template context
- [ ] BDD happy path: MFA setup page shows otpauth URI

## Dependencies

- #70 — MFA UI pages

## Labels

`feature:mfa`, `layer:ui`, `size:S`
