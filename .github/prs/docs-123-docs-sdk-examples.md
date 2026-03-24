## docs(sdk): client integration examples (Python, JavaScript, Go, cURL)

## Summary

Code examples showing how to integrate with Shomer from common languages and tools. Covers OAuth2 flows, token usage, and API calls.

## Changes

- [ ] cURL examples for all OAuth2 flows
- [ ] Python example (using `requests` or `httpx`)
- [ ] JavaScript/TypeScript example (using `fetch` or `openid-client`)
- [ ] Go example (using `golang.org/x/oauth2`)
- [ ] Example: Authorization Code + PKCE (web app)
- [ ] Example: Client Credentials (backend service)
- [ ] Example: Device Code (CLI tool)
- [ ] Example: using PATs for API access
- [ ] Example: validating JWT access tokens as a resource server

## Dependencies

- #105 - OAuth2 flows guide (for context)

## Related Issue

Closes #123

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present


