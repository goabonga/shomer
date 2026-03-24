# feat(pat): PAT authentication middleware

## Description

Middleware that authenticates requests using Personal Access Tokens. Integrates with get_current_user so PATs work alongside Bearer JWT and session auth.

## Objective

Enable API access via PATs as a third authentication method.

## Tasks

- [ ] Detect PAT in Authorization header (Bearer shm_pat_...)
- [ ] Validate PAT via PAT service
- [ ] Set current user context with PAT scopes
- [ ] Update last_used_at
- [ ] Integration with get_current_user priority chain
- [ ] Unit tests

## Dependencies

- #75 — PAT service
- #42 — get_current_user dependency

## Labels

`feature:pat`, `rfc:6750`, `type:infra`, `size:M`
