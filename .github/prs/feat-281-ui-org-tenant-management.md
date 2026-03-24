## feat(ui): organisation/tenant self-service management in settings

## Summary

- Add user-facing tenant/organisation management to the settings UI
- Includes ~30 routes: list orgs, create org, detail/edit, members, roles, IdP, branding, trust policies, custom domains, email templates

## Changes

- [ ] GET /ui/settings/organisations list
- [ ] POST create organisation
- [ ] GET/POST org detail/edit
- [ ] Custom domain verification
- [ ] Member management (add/remove/update role)
- [ ] Role management (CRUD + scope assignment)
- [ ] IdP management (CRUD + toggle)
- [ ] Branding customization
- [ ] Trust policies
- [ ] Email template management
- [ ] Unit tests
- [ ] BDD tests

## Dependencies

- #79 — models tenant
- #82 — tenant branding
- #83 — tenant trust policy
- #84 — models identity provider

## Related Issue

Closes #281

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present
