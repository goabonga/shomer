# docs(api): OpenAPI/Swagger auto-generated API reference

## Description

Set up auto-generated API reference documentation from FastAPI's OpenAPI schema, integrated into MkDocs. Ensures all endpoints have proper descriptions, request/response examples, and error codes.

## Objective

Provide always-up-to-date API documentation generated directly from the code.

## Tasks

- [ ] Ensure all routes have OpenAPI summary, description, and tags
- [ ] Add request/response examples to schemas
- [ ] Document error responses (4xx, 5xx) per endpoint
- [ ] Integrate OpenAPI spec into MkDocs (swagger-ui or redoc plugin)
- [ ] Add authentication requirements per endpoint (Bearer, session, client)
- [ ] Group endpoints by tag (auth, oauth2, oidc, mfa, admin, etc.)

## Dependencies

- All route issues (M3–M19) should be substantially complete

## Labels

`type:docs`, `layer:api`, `size:L`
