# docs(architecture): system architecture and design decisions

## Description

High-level architecture document covering system components, data flow, technology choices, and design decisions. Includes diagrams (Mermaid) for request flows, component interactions, and deployment topology.

## Objective

Give developers and operators a clear mental model of how Shomer is structured and why.

## Tasks

- [ ] Component overview diagram (FastAPI, Celery, PostgreSQL, Redis)
- [ ] Request lifecycle diagram (auth flow, token flow)
- [ ] Database schema ER diagram (Mermaid)
- [ ] Design decisions and trade-offs (why Argon2id, why RS256, why async SQLAlchemy)
- [ ] Security architecture (encryption at rest, token storage, secret management)
- [ ] Multi-tenancy architecture (tenant isolation, resolution strategy)
- [ ] File/module structure documentation

## Dependencies

None — can be written at any point.

## Labels

`type:docs`, `size:L`
