---
icon: lucide/plug
---

# Dependency injection

Nothing in Shomer constructs its own collaborators. A handler, a command
or a worker names the interface it needs; the container supplies whatever
is bound to it. Wiring goes through
[tripack](https://github.com/goabonga/tripack), a typed IoC container.

## The three contracts

`shomer_lib.contracts` declares what a service is allowed to depend on.
They are `Protocol`s, so an implementation satisfies one by shape and
never has to import it.

| Contract | What it answers |
| --- | --- |
| `Settings` | The issuer and the database URL this process resolved. |
| `Clock` | The current time — as an interface, so a test can move it. |
| `Database` | Units of work against the backing database. |

`Clock` is the one that looks like overkill and is not. Token lifetimes,
session expiry and audit ordering all read the time, and a test that
cannot move the clock cannot assert any of them.

## One place decides

`shomer_lib.module.ShomerModule` binds each contract to its default
implementation. It is the only file that names `EnvSettings`,
`SystemClock` and `SqlAlchemyDatabase`; everything else sees interfaces.

```python
from shomer_lib.contracts import Settings
from shomer_lib.module import build_container

with build_container() as container:
    print(container.resolve(Settings).issuer)
```

All three bindings are singletons. The database owns a connection pool
that exists to be shared — a transient binding would open a new pool per
resolution and leak every one of them.

The `with` block is not decoration. Closing the container is what
disposes that pool: the container tears a singleton down by calling
`close()` on it, and a process that skips the block leaves sockets open
until it is reaped.

## In the HTTP services

`shomer-api` and `shomer-ssr` are built on `TripackAPI`, which owns the
container's lifecycle and resolves the marked parameters of every route.

```python
from typing import Annotated
from tripack_container import Inject
from shomer_lib.contracts import Clock


@app.get("/healthz")
def healthz(clock: Annotated[Clock, Inject]) -> dict[str, object]:
    return {"status": "ok", "time": clock.now()}
```

The lifespan is what builds the container, which is why a test has to
enter the app as a context manager. Without it every injected parameter
fails to resolve, and the failure reads as a routing problem.

## In the CLI and the worker

Neither has a request lifecycle, so both build a container, use it and
close it.

```python
with build_container() as container:
    cli(obj=container)          # reaches commands via @click.pass_obj
```

## Adding a dependency

1. Declare the interface in `shomer_lib.contracts`.
2. Write the implementation next to it.
3. Bind the two in `ShomerModule`.

Step 3 is the only place the choice is recorded, which is what makes it
reversible.

## A note for type checkers

Passing a `Protocol` where a `type[T]` is expected — which is what
binding and resolving an interface both do — is reported by mypy as
`type-abstract`. The rule it enforces is about not instantiating an
abstract type, and does not apply when the class is a key rather than a
constructor, so the code is disabled workspace-wide in `pyproject.toml`.
Actually instantiating a `Protocol` is a different error code and is
still caught.
