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
| [**Dependency injection**](injection.md) | How a service names what it needs and where the answer is decided. |
| [**Changelog**](changelog.md) | What changed, per release. |
| [**Versions**](versions.md) | The current version of every component. |

## The shape of it

The repository is a [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/). Each package carries its own version, its own
changelog and its own release tag, and is published independently.

| Package | Kind | What it is |
| --- | --- | --- |
| `shomer-lib` | Python | Contracts, settings, ORM models, database connector, DI module. |
| `shomer-bdd` | Python | The Alembic revisions and their runner. |
| `shomer-api` | Python | The OpenID Connect / OAuth 2.0 endpoints. |

## How the pieces find each other

Nothing here constructs its own collaborators. Every service installs
[`ShomerModule`](injection.md) and names the interface it needs — the
container supplies the implementation. That is what makes the settings a
process resolved inspectable (`shomer config`), a fake clock possible in
a test, and a database swap a single edit rather than a search.

## Honestly, today

The OAuth 2.0 / OIDC grants are **not implemented yet**. What exists is
the workspace, the wiring, the schema, the discovery document, and the
release machinery that publishes all of it.
