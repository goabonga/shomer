## docs(api): OpenAPI/Swagger auto-generated API reference

## Summary

Set up auto-generated API reference documentation from FastAPI's OpenAPI schema, integrated into MkDocs. Ensures all endpoints have proper descriptions, request/response examples, and error codes.

## Changes

- [ ] Ensure all routes have OpenAPI summary, description, and tags
- [ ] Add request/response examples to schemas
- [ ] Document error responses (4xx, 5xx) per endpoint
- [ ] Integrate OpenAPI spec into MkDocs (swagger-ui or redoc plugin)
- [ ] Add authentication requirements per endpoint (Bearer, session, client)
- [ ] Group endpoints by tag (auth, oauth2, oidc, mfa, admin, etc.)

## Dependencies

- All route issues (M3–M19) should be substantially complete

## Related Issue

Closes #114

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present


