---
icon: lucide/tags
---

# Versions

Every component is versioned on its own. The numbers below are written by
[multicz](https://github.com/goabonga/multicz) at release time — nothing
here is maintained by hand, and none of it can drift from the version the
component itself reports.

| Component | Version | Tag |
| --- | --- | --- |
| `shomer-lib` | {{ config.extra.versions.lib }} | `lib-v{{ config.extra.versions.lib }}` |
| `shomer-bdd` | {{ config.extra.versions.bdd }} | `bdd-v{{ config.extra.versions.bdd }}` |
| `shomer-api` | {{ config.extra.versions.api }} | `api-v{{ config.extra.versions.api }}` |
| `shomer-cli` | {{ config.extra.versions.cli }} | `cli-v{{ config.extra.versions.cli }}` |
| `shomer-job` | {{ config.extra.versions.job }} | `job-v{{ config.extra.versions.job }}` |
| `shomer-ssr` | {{ config.extra.versions.ssr }} | `ssr-v{{ config.extra.versions.ssr }}` |
| `shomer-web` | {{ config.extra.versions.web }} | `web-v{{ config.extra.versions.web }}` |
| this site | {{ config.extra.versions.docs }} | `docs-v{{ config.extra.versions.docs }}` |

## How a version is decided

The commit type decides the bump: `feat` a minor, `fix` and `perf` a
patch, `feat!` or a `BREAKING CHANGE:` footer a major. Everything else
documents the change without releasing it.

Which component a commit bumps is decided by the paths it touches, not by
the scope written in the subject — and rarely only one. A commit under
`packages/web/src/` bumps `web`; because `ssr` declares a dependency on
it, `ssr` is released in the same pass so the published wheel actually
contains the new bundle.

`shomer-lib` sits at the root of that graph. It owns the contracts every
other package types against, so a change there can alter what a service
observes even when the service's own sources did not move. Everything
downstream is therefore released with it:

```
lib ──┬── bdd ──┐
      ├── api ──┤
      ├── cli ──┼── docs
      ├── job ──┤
      └── ssr ──┘
             │
web ─────────┘
```
