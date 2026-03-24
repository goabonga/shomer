## fix(infra): Makefile install target missing --extras worker

## Summary

The `make install` target only installs the `server` extra. Add `--extras worker` so Celery dependencies are available locally.

## Changes

- [ ] Update the `install` target in `Makefile` to include `--extras worker`
- [ ] Verify `make install && make test` passes with Celery imports

## Dependencies

None.

## Related Issue

Closes #143

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present
