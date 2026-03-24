## feat(ui): avatar upload on profile settings page

## Summary

- Add avatar/profile picture upload to the profile settings page
- Support JPEG, PNG, GIF, WebP (max 5MB) with preview and fallback display

## Changes

- [ ] File upload form on profile page
- [ ] POST /ui/settings/profile/avatar handler
- [ ] Image validation (type, size)
- [ ] Store uploaded file and update picture_url
- [ ] Display current avatar with fallback
- [ ] Unit tests
- [ ] BDD tests

## Dependencies

- #257 — UI profile settings all fields

## Related Issue

Closes #282

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present
