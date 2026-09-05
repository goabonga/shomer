# syntax=docker/dockerfile:1
#
# Multi-stage build on Chainguard distroless images.
#
# - builder uses python:latest-dev (it has pip and a shell) to install the
#   wheel into a portable venv at /app/venv.
# - runtime uses python:latest — distroless: no shell, no package manager,
#   nothing to pivot into. Both are rebuilt daily by Chainguard and run as
#   the nonroot user (UID 65532).
#
# Both are pinned by digest. A floating tag means two builds of the same
# commit can produce different images, which is the thing an SBOM and a
# signature exist to rule out — and it is what DL3007 is about. Dependabot
# watches the digests and raises the bump as a pull request.
#
# The build context is `packages/`, not this directory: shomer-api depends on
# shomer-lib, a workspace package that is not on PyPI, so it has to be
# copied in beside it.
#
#   docker build -f packages/api/Dockerfile -t api packages

FROM cgr.dev/chainguard/python:latest-dev@sha256:aa89119db7f7fb4a6628ac82e2c38404cc64cd56ccd858d2c78646776b3fffef AS builder

WORKDIR /app
COPY lib ./lib
COPY api ./api

# Both paths in one pip invocation: shomer-lib is not published, so
# resolving shomer-api on its own would send pip to PyPI for a package that is
# not there. Given both, it satisfies the dependency from the local tree.
RUN python -m venv /app/venv \
 && /app/venv/bin/pip install --no-cache-dir ./lib ./api

FROM cgr.dev/chainguard/python:latest@sha256:115532a106aff6e820cd637809edd0c9239f2269d46fb9937cac703cc4d101e5

COPY --from=builder /app/venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

EXPOSE 8000

# OCI annotations. Declared here rather than in the workflow so a local
# `docker build` carries them too — and, the Dockerfile being in this
# component's multicz paths, so that editing them actually releases an
# image that has them.
#
# The three values that cannot be static are passed as build args by the
# `api-container` CI job; a local build simply leaves them empty.
ARG VERSION=""
ARG REVISION=""
ARG CREATED=""

LABEL org.opencontainers.image.title="shomer-api" \
      org.opencontainers.image.description="Shomer authorization API (OpenID Connect / OAuth 2.0 endpoints)." \
      org.opencontainers.image.source="https://github.com/goabonga/shomer" \
      org.opencontainers.image.url="https://github.com/goabonga/shomer" \
      org.opencontainers.image.documentation="https://goabonga.github.io/shomer/" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.vendor="goabonga" \
      org.opencontainers.image.version="$VERSION" \
      org.opencontainers.image.revision="$REVISION" \
      org.opencontainers.image.created="$CREATED"

ENTRYPOINT ["shomer-api"]
