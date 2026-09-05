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
| this site | {{ config.extra.versions.docs }} | `docs-v{{ config.extra.versions.docs }}` |

## How a version is decided

The commit type decides the bump: `feat` a minor, `fix` and `perf` a
patch, `feat!` or a `BREAKING CHANGE:` footer a major. Everything else
documents the change without releasing it.

Which component a commit bumps is decided by the paths it touches, not by
the scope written in the subject
