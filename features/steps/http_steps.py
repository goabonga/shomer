# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

import json
import urllib.request

from behave import then, when


@when('I send a GET request to "{path}"')
def step_get_request(context, path):
    url = context.base_url + path
    req = urllib.request.Request(url)
    context.response = urllib.request.urlopen(req)
    context.response_body = context.response.read().decode()


@when('I send a POST request to "{path}"')
def step_post_request(context, path):
    url = context.base_url + path
    req = urllib.request.Request(url, method="POST")
    context.response = urllib.request.urlopen(req)
    context.response_body = context.response.read().decode()


@when('I send a DELETE request to "{path}"')
def step_delete_request(context, path):
    url = context.base_url + path
    req = urllib.request.Request(url, method="DELETE")
    context.response = urllib.request.urlopen(req)
    context.response_body = context.response.read().decode()


@then("the response status code should be {status_code:d}")
def step_check_status_code(context, status_code):
    assert context.response.status == status_code


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
