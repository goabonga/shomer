## chore(ci): skip CI workflows on draft pull requests

## Summary

Configure GitHub Actions workflows to skip execution when a pull request is in draft state. CI only runs when the PR is marked as "Ready for review".

## Changes

- [ ] Add `if: github.event.pull_request.draft == false` condition to CI workflows
- [ ] Ensure CI triggers when a PR is moved from draft to ready
- [ ] Verify CI still runs on pushes to `main`

## Dependencies

None.

## Related Issue

Closes #0

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present
