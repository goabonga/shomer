## fix(bdd): add wait_for_url to Playwright steps for CI stability

## Summary

Make Playwright BDD steps more robust against slow redirects in CI by adding explicit waits after navigation-triggering actions.

## Changes

- [ ] Add page.wait_for_url after click steps
- [ ] Improve click button step with navigation wait
- [ ] Verify CI stability

## Related Issue

Closes #203

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present
