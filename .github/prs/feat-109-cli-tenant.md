## feat(cli): shomer tenant - tenant management commands

## Summary

CLI commands for tenant management: CRUD for tenants, member management, domain configuration, and branding.

## Changes

- [ ] `shomer tenant list` - list tenants
- [ ] `shomer tenant get <slug>` - show tenant details (members, domains, branding)
- [ ] `shomer tenant create <slug>` - create tenant (--name, --domain)
- [ ] `shomer tenant update <slug>` - update tenant settings
- [ ] `shomer tenant delete <slug>` - delete tenant (with --confirm)
- [ ] `shomer tenant add-member <slug> <email> --role <role>` - add member
- [ ] `shomer tenant remove-member <slug> <email>` - remove member
- [ ] `shomer tenant list-members <slug>` - list tenant members
- [ ] `shomer tenant add-domain <slug> <domain>` - add custom domain
- [ ] `shomer tenant verify-domain <slug> <domain>` - trigger DNS verification
- [ ] Rich table output
- [ ] Unit tests

## Dependencies

- #79 - Tenant model
- #80 - tenant resolution

## Related Issue

Closes #109

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present


