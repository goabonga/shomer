# Shomer

**Shomer** (*שׁוֹמֵר*) is Hebrew for *guardian*, *watchman* — the one who
keeps watch over the gate.

Shomer is an **OpenID Connect / OAuth 2.0** platform.

## Packages

The repository is a [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/).
Every package is versioned, changelogged, tagged and released on its own.

| Package | Kind | What it is |
| --- | --- | --- |
| [`shomer-lib`](packages/lib) | Python | Contracts, settings, ORM models, database connector, DI module. |
| [`shomer-bdd`](packages/bdd) | Python | The Alembic revisions and their runner. |

`shomer-lib` sits at the root: every service names an interface it
declares and lets the container supply the implementation, so a service
never mentions a concrete class and swapping one is a change in a single
place.

## Dependency injection

Wiring goes through [tripack](https://github.com/goabonga/tripack), the
typed IoC container. `shomer_lib.module.ShomerModule` is the one place
that decides which implementation answers which contract; services
install it and ask for what they need.

```python
from shomer_lib.contracts import Settings
from shomer_lib.module import build_container

with build_container() as container:
    print(container.resolve(Settings).issuer)
```
