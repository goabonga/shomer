# feat(ui): organisation/tenant self-service management in settings

## Description

User-facing tenant management: list orgs, create org, view/edit org details, manage members, roles, IdP, branding, trust policies, custom domains, email templates. ~30 routes matching auth/ project.

## Objective

Provide full self-service tenant/organisation management from the settings UI, allowing users to create and manage their own organisations without admin intervention.

## Tasks

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

## Labels

`feature:ui`, `feature:tenant`, `layer:ui`, `size:XL`
