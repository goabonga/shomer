# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""Step implementations for the shomer-api end-to-end suite."""

from __future__ import annotations

import re

from behave import given, then, when

ENDPOINT_KEYS = ("authorization_endpoint", "token_endpoint", "jwks_uri")


@given("shomer-api is reachable at SHOMER_API_URL")
def step_reachable(context) -> None:
    response = context.client.get("/healthz")
    assert response.status_code == 200, (
        f"liveness check failed against {context.base_url}: "
        f"status={response.status_code} body={response.text!r}"
    )


@when('I GET "{path}"')
def step_get(context, path: str) -> None:
    context.response = context.client.get(path)


@then("the response status is {status:d}")
def step_status(context, status: int) -> None:
    assert context.response.status_code == status, (
        f"unexpected status: got {context.response.status_code} want {status} "
        f"(body={context.response.text!r})"
    )


# `{key:S}` is behave's non-whitespace parse type. With the default `{key}`
# — a lazy `.+?` — this pattern swallows the trailing qualifier of the
# longer steps below, and behave rejects the whole set as ambiguous at
# registration time.
@then('the JSON body has key "{key:S}"')
def step_has_key(context, key: str) -> None:
    body = context.response.json()
    assert key in body, f"missing key {key!r} in body {body!r}"


@then('the JSON body has key "{key}" equal to "{value}"')
def step_key_equals(context, key: str, value: str) -> None:
    body = context.response.json()
    assert body.get(key) == value, f"{key}: got {body.get(key)!r} want {value!r}"


@then('the JSON body has key "{key}" matching "{pattern}"')
def step_key_matches(context, key: str, pattern: str) -> None:
    value = context.response.json().get(key)
    assert isinstance(value, str), f"{key} is not a string: {value!r}"
    assert re.match(pattern, value), f"{key}={value!r} does not match /{pattern}/"


@then('the JSON body has key "{key}" containing "{element}"')
def step_key_contains(context, key: str, element: str) -> None:
    value = context.response.json().get(key)
    assert isinstance(value, list), f"{key} is not a list: {value!r}"
    assert element in value, f"{key}={value!r} does not contain {element!r}"


@then("the discovery endpoints all start with the issuer")
def step_endpoints_share_issuer(context) -> None:
    body = context.response.json()
    issuer = body["issuer"]
    assert issuer.startswith("http"), f"issuer is not absolute: {issuer!r}"
    for key in ENDPOINT_KEYS:
        value = body[key]
        assert value.startswith(f"{issuer}/"), (
            f"{key}={value!r} is not under the issuer {issuer!r} — a client "
            "comparing `iss` byte-for-byte will reject tokens from here"
        )
