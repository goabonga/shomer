## feat(ui): advanced PAT features (expiration presets, regenerate, bulk revoke, usage stats)

## Summary

- Enhance PAT management page with expiration date presets (7/30/60/90 days, 1 year, no expiration)
- Add token regeneration, bulk revoke all, and usage statistics (use count, last used date/IP)

## Changes

- [ ] Expiration presets dropdown on create form
- [ ] Token regenerate action
- [ ] Bulk "Revoke All" button
- [ ] Usage stats display (use_count, last_used_at, last_used_ip)
- [ ] Unit tests
- [ ] BDD tests

## Dependencies

- #78 — UI PAT management

## Related Issue

Closes #283

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present
