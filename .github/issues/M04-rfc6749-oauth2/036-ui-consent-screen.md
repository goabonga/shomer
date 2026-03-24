# feat(oauth2): [UI] consent screen

## Description

Jinja2/HTMX consent page showing the requesting client, requested scopes, and Authorize/Deny buttons. Supports tenant branding.

## Objective

Provide the user-facing consent UI for the OAuth2 authorization flow.

## Tasks

- [ ] Consent page template with client info and scope list
- [ ] Authorize and Deny buttons (POST form)
- [ ] Tenant branding support (logo, colors)
- [ ] Scope descriptions (human-readable)
- [ ] CSRF token in form

## Dependencies

- #32 — consent API

## Labels

`rfc:6749`, `feature:oauth2`, `layer:ui`, `size:M`
