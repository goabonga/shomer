## docs(architecture): system architecture and design decisions

## Summary

High-level architecture document covering system components, data flow, technology choices, and design decisions. Includes diagrams (Mermaid) for request flows, component interactions, and deployment topology.

## Changes

- [ ] Component overview diagram (FastAPI, Celery, PostgreSQL, Redis)
- [ ] Request lifecycle diagram (auth flow, token flow)
- [ ] Database schema ER diagram (Mermaid)
- [ ] Design decisions and trade-offs (why Argon2id, why RS256, why async SQLAlchemy)
- [ ] Security architecture (encryption at rest, token storage, secret management)
- [ ] Multi-tenancy architecture (tenant isolation, resolution strategy)
- [ ] File/module structure documentation

## Dependencies

None - can be written at any point.

## Related Issue

Closes #112

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present


