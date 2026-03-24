# chore(ci): skip CI workflows on draft pull requests

## Description

Configure GitHub Actions workflows to skip execution when a pull request is in draft state. CI should only run when the PR is marked as "Ready for review" to save runner minutes and reduce noise.

## Objective

Avoid wasting CI resources on work-in-progress branches that are not yet ready for validation.

## Tasks

- [ ] Add `if: github.event.pull_request.draft == false` condition to CI workflows
- [ ] Ensure CI triggers when a PR is moved from draft to ready
- [ ] Verify CI still runs on pushes to `main`

## Dependencies

None.

## Labels

`type:infra`, `size:S`
