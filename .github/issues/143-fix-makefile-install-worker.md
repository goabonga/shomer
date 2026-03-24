# fix(infra): Makefile install target missing --extras worker

## Description

The `make install` target only installs the `server` extra. The `worker` extra (Celery) is missing, which causes import errors when running Celery-related code or tests locally.

## Objective

Ensure `make install` installs all extras so the full application can run locally.

## Tasks

- [ ] Update the `install` target in `Makefile` to include `--extras worker`
- [ ] Verify `make install && make test` passes with Celery imports

## Dependencies

None.

## Labels

`type:infra`, `size:S`
