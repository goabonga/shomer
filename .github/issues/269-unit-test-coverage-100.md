# test(unit): achieve 100% unit test coverage across all source files

## Description

Current unit test coverage is at ~93%. Many source files in `src/shomer/` have untested branches, error paths, or edge cases. This issue covers writing unit tests (pure mock, no database or HTTP) to reach 100% line and branch coverage across all modules.

## Objective

Reach 100% unit test coverage (`make test` reports `TOTAL 100%`) by writing missing tests for all uncovered lines and branches.

## Tasks

- [ ] Identify all files with <100% coverage via `make test` HTML report
- [ ] Write unit tests for `services/` uncovered lines (revocation, trust_policy, tenant_branding, tenant_resolver, token_exchange, token_service)
- [ ] Write unit tests for `routes/` uncovered lines (auth, oauth2, federation, mfa, device)
- [ ] Write unit tests for `middleware/` uncovered lines (rbac, bearer, session, cors)
- [ ] Write unit tests for `core/` uncovered lines (security, database, settings)
- [ ] Write unit tests for `models/` uncovered lines (queries, relationships)
- [ ] Verify 100% coverage with `make test`

## Dependencies

None — this is a standalone quality improvement.

## Labels

`type:test`, `layer:test`, `size:XL`, `priority:medium`
