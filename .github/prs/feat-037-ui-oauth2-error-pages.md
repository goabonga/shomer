## feat(oauth2): [UI] OAuth2 error pages

## Summary

Error pages for OAuth2 error cases: invalid_client, invalid_redirect_uri, access_denied, server_error. Clear messages conforming to RFC 6749.

## Changes

- [ ] Generic OAuth2 error page template
- [ ] Specific messages for invalid_client, invalid_redirect_uri
- [ ] Error code and description display
- [ ] Tenant branding support

## Dependencies

- #31 - authorization endpoint

## Related Issue

Closes #37

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present


