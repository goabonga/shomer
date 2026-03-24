# feat(oauth2): POST /oauth2/par

## Description

PAR endpoint per RFC 9126. Receives authorization parameters via POST, authenticates the client, validates parameters, stores the request, and returns request_uri + expires_in.

## Objective

Allow clients to push authorization parameters server-side before redirecting the user.

## Tasks

- [ ] POST `/oauth2/par` route
- [ ] Client authentication
- [ ] Parameter validation (same rules as /authorize)
- [ ] Store PARRequest with generated request_uri
- [ ] Return request_uri + expires_in
- [ ] Integration test

## Dependencies

- #28 — client service
- #57 — PARRequest model

## Labels

`rfc:9126`, `type:route`, `layer:api`, `size:M`
