# shomer-web

[![CI](https://github.com/goabonga/shomer/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/goabonga/shomer/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/goabonga/shomer/blob/main/LICENSE)

TypeScript/React sources for the pages
[Shomer](https://github.com/goabonga/shomer) serves — an OpenID Connect /
OAuth 2.0 platform.

This package is **not published**. It builds into
[`shomer-ssr`](https://github.com/goabonga/shomer/tree/main/packages/ssr)
and ships inside that wheel, which is why it carries its own version and
tag: the tag is how a reader tells which frontend a given wheel contains.

## Build

```bash
npm ci                                    # from the repository root
npm run build --workspace packages/web
```

Outputs land in `packages/ssr/src/shomer_ssr/{static,templates}/`. Those
directories are build products — edit the sources here, never the copies
there.

For an incremental loop:

```bash
node packages/web/scripts/build.mjs --watch
```

The watch build writes a sourcemap without appending the
`//# sourceMappingURL=` comment, so the bundle stays byte-identical
between dev and release and no dev artefact rides into a release commit.
The server advertises the map with a `SourceMap` response header instead,
which devtools honour identically.

## Checks

```bash
npm run lint --workspace packages/web
npm run format:check --workspace packages/web
npm run typecheck --workspace packages/web
npm run test --workspace packages/web
```

## Documentation

Project site: <https://goabonga.github.io/shomer/>.

## License

MIT — see [LICENSE](https://github.com/goabonga/shomer/blob/main/LICENSE).
