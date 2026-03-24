# fix(bdd): add wait_for_url to Playwright steps for CI stability

## Description

Consent flow BDD scenario intermittently fails in CI due to slow redirects.

## Tasks

- [ ] Add page.wait_for_url after click steps that trigger redirects
- [ ] Add explicit wait in click button step for navigation
- [ ] Verify consent flow passes reliably in CI
