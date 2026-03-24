# feat(oauth2): [UI] OAuth2 error pages

## Description

Error pages for OAuth2 error cases: invalid_client, invalid_redirect_uri, access_denied, server_error. Clear messages conforming to RFC 6749.

## Objective

Provide user-friendly error pages when the authorization flow cannot redirect back to the client.

## Tasks

- [ ] Generic OAuth2 error page template
- [ ] Specific messages for invalid_client, invalid_redirect_uri
- [ ] Error code and description display
- [ ] Tenant branding support

## Dependencies

- #31 — authorization endpoint

## Labels

`rfc:6749`, `layer:ui`, `size:S`
