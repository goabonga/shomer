---
icon: lucide/rocket
---

# Getting started

## Requirements

- Python **3.13+**
- [uv](https://docs.astral.sh/uv/)
- Node **22+**

## Clone and install

The Python and TypeScript workspaces are installed separately — they are
two package managers over the same tree, not one wrapping the other.

```bash
git clone https://github.com/goabonga/shomer.git
cd shomer

uv sync --all-packages   # Python packages + dev tooling
npm ci                   # TypeScript packages, hoisted at the root
```

## Work on the frontend

```bash
node packages/web/scripts/build.mjs --watch
```

The watch build rewrites `packages/ssr/src/shomer_ssr/{static,templates}/`
on every change. Never edit those two directories directly — they are
build outputs, and the next build overwrites them.

## The gates

These are exactly what CI runs; running them locally is the only way to
find out before the pipeline does.

```bash

npm run lint --workspace packages/web
npm run format:check --workspace packages/web
npm run typecheck --workspace packages/web
npm run test --workspace packages/web
```

Install the hooks once and most of it runs on commit:

```bash
uv run pre-commit install
```
