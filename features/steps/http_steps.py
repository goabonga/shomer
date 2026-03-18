# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

import json
import urllib.error
import urllib.request

from behave import given, then, when


def _send(context, method, path, data=None):
    """Send an HTTP request and store response on context."""
    url = context.base_url + path
    headers = {}
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        context.response = urllib.request.urlopen(req)
        context.response_status = context.response.status
        context.response_body = context.response.read().decode()
    except urllib.error.HTTPError as e:
        context.response = e
        context.response_status = e.code
        context.response_body = e.read().decode()


@given("I have a JSON payload")
def step_set_json_payload(context):
    context.json_payload = json.loads(context.text)


@when('I send a GET request to "{path}"')
def step_get_request(context, path):
    _send(context, "GET", path)


@when('I send a POST request to "{path}"')
def step_post_request(context, path):
    data = getattr(context, "json_payload", None)
    _send(context, "POST", path, data=data)
    context.json_payload = None


@when('I send a POST request to "{path}" with JSON')
def step_post_request_with_json(context, path):
    data = json.loads(context.text)
    _send(context, "POST", path, data=data)


@when('I send a DELETE request to "{path}"')
def step_delete_request(context, path):
    _send(context, "DELETE", path)


@then("the response status code should be {status_code:d}")
def step_check_status_code(context, status_code):
    assert context.response_status == status_code


@then('the response body should contain "{text}"')
def step_check_response_body(context, text):
    assert text in context.response_body


@then('the response should have JSON key "{key}"')
def step_check_json_key(context, key):
    data = json.loads(context.response_body)
    assert key in data, f"Key '{key}' not found in {data}"


@then("the response content type should be html")
def step_check_html_content_type(context):
    content_type = context.response.headers.get("Content-Type", "")
    assert "text/html" in content_type


@then("the response content type should be json")
def step_check_json_content_type(context):
    content_type = context.response.headers.get("Content-Type", "")
    assert "application/json" in content_type


@then('the response should have header "{name}" containing "{value}"')
def step_check_response_header(context, name, value):
    header = context.response.headers.get(name, "")
    assert value in header, f"Header '{name}' = '{header}' does not contain '{value}'"
