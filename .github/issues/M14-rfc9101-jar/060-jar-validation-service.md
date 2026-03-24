# feat(oauth2): JAR validation service (JWT request object)

## Description

Service for validating JWT Request Objects (JAR). Verifies signature (client public key or JWKS), validates claims (iss=client_id, aud=issuer), extracts authorization parameters from the JWT.

## Objective

Provide a reusable service for validating JWTs submitted as request objects in /authorize.

## Tasks

- [ ] JWT request object parsing
- [ ] Signature verification using client's registered JWKS or jwks_uri
- [ ] Claims validation (iss must equal client_id, aud must equal issuer)
- [ ] Extract authorization parameters from JWT payload
- [ ] Error handling with specific error codes
- [ ] Unit tests

## Dependencies

- #15 — JWT validation service
- #28 — client service

## Labels

`rfc:9101`, `type:service`, `size:L`
