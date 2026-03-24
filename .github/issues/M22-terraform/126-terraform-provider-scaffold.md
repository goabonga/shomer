# feat(terraform): Terraform provider scaffold and authentication

## Description

Scaffold the Shomer Terraform provider using the Terraform Plugin Framework (Go). Set up provider configuration (API URL, authentication via PAT or client credentials), HTTP client, and CI/CD for building and publishing.

## Objective

Establish the provider foundation that all Terraform resources and data sources will use.

## Tasks

- [ ] Go module with Terraform Plugin Framework
- [ ] Provider schema: `url`, `token`, `client_id`, `client_secret`
- [ ] Authentication via PAT (Bearer token)
- [ ] Authentication via client_credentials grant (for CI/CD pipelines)
- [ ] HTTP client with retry, timeout, and error mapping
- [ ] Provider documentation (Terraform Registry format)
- [ ] CI: build, lint, test, goreleaser
- [ ] Acceptance test framework setup
- [ ] Publish to Terraform Registry (GitHub release-based)

## Dependencies

- #102 — CLI/API client patterns (shared API surface)

## Labels

`type:infra`, `size:L`
