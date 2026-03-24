# feat(oauth2): token exchange validation and scope escalation service

## Description

Token Exchange service: validates the subject_token, checks exchange permissions for the client, computes resulting scopes (intersection or controlled escalation), supports impersonation and delegation.

## Objective

Encapsulate token exchange business logic independently of the token endpoint.

## Tasks

- [ ] Subject token validation (JWT verification)
- [ ] Client permission check for token exchange
- [ ] Scope computation (intersection of requested vs allowed)
- [ ] Impersonation support (act-as)
- [ ] Delegation support (on-behalf-of with actor claim)
- [ ] Unit tests

## Dependencies

- #15 — JWT validation

## Labels

`rfc:8693`, `type:service`, `size:L`
