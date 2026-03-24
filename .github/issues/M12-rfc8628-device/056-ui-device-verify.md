# feat(oauth2): [UI] device code verification page

## Description

Jinja2/HTMX page for user_code entry by the user. Shows the requesting client, scopes, and Authorize/Deny buttons. Accessible via verification_uri.

## Objective

Provide the browser UI where users approve or deny device authorization requests.

## Tasks

- [ ] User code input page (accessible via verification_uri)
- [ ] Auto-fill user_code if verification_uri_complete is used
- [ ] Display client info and requested scopes
- [ ] Authorize and Deny buttons
- [ ] Success and error states
- [ ] Requires authenticated session (redirect to login if needed)

## Dependencies

- #54 — device authorization endpoint

## Labels

`rfc:8628`, `layer:ui`, `size:M`
