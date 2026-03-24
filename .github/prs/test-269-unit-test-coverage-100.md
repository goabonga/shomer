## test(unit): achieve 100% unit test coverage across all source files

## Summary

Write missing unit tests to reach 100% line coverage across all `src/shomer/` modules. Pure mock tests — no database, no HTTP client.

## Changes

- [ ] Identify all files with <100% coverage via `make test` HTML report
- [ ] Write unit tests for `services/` uncovered lines
- [ ] Write unit tests for `routes/` uncovered lines
- [ ] Write unit tests for `middleware/` uncovered lines
- [ ] Write unit tests for `core/` uncovered lines
- [ ] Write unit tests for `models/` uncovered lines
- [ ] Verify 100% coverage with `make test`

## Dependencies

None

## Related Issue

Closes #269

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass with 100% coverage
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present
