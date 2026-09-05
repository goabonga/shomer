---
icon: lucide/house
---

# Shomer

**Shomer** (*שׁוֹמֵר*) is Hebrew for *guardian*, *watchman* — the one who
keeps watch over the gate.

Shomer is an **OpenID Connect / OAuth 2.0** platform.

> Released under the [MIT License](https://github.com/goabonga/shomer/blob/main/LICENSE) ·
> Source on [GitHub](https://github.com/goabonga/shomer)

---

## Where to go

| | |
|---|---|
| [**Getting started**](getting-started.md) | Clone the workspace, build the frontend, run the services. |
| [**Changelog**](changelog.md) | What changed, per release. |
| [**Versions**](versions.md) | The current version of every component. |

## The shape of it

The repository is a [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/). Each package carries its own version, its own
changelog and its own release tag, and is published independently.

| Package | Kind | What it is |
| --- | --- | --- |

## Honestly, today

The OAuth 2.0 / OIDC grants are **not implemented yet**. What exists is
the workspace, the wiring, the schema, the discovery document, and the
release machinery that publishes all of it.
