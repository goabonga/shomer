# feat(auth): get_current_user dependency (Bearer + session)

## Description

FastAPI dependency that resolves the current user from either a Bearer JWT token or a session cookie. Bearer takes priority if both are present. Exposes user_id, scopes, and tenant_id.

## Objective

Provide a unified authentication dependency for all protected routes regardless of auth method.

## Tasks

- [ ] Try Bearer token first → validate JWT, extract user_id and scopes
- [ ] Fall back to session cookie → validate session, extract user_id
- [ ] Return 401 if neither is valid
- [ ] Expose user_id, scopes, tenant_id in a CurrentUser object
- [ ] Optional variant (`get_optional_user`) that returns None instead of 401
- [ ] Unit tests

## Dependencies

- #15 — JWT validation service
- #20 — session service
- #41 — Bearer middleware

## Labels

`rfc:6750`, `type:infra`, `size:M`
