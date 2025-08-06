# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

from pathlib import Path

from behave import then, when

__expected_version__: str = "0.0.0"

SCREENSHOTS_DIR = Path("screenshots")


@when('I open the page "{path}"')
def step_open_page(context, path):
    context.page = context.browser.new_page()
    context.page.goto(context.base_url + path)


@then('the page title should be "{title}"')
def step_check_page_title(context, title):
    assert context.page.title() == title


@then('the page should contain "{text}"')
def step_check_page_content(context, text):
    assert context.page.text_content("body") is not None
    assert text in context.page.text_content("body")


@then("the page should contain the current version")
def step_check_page_version(context):
    expected = f"v{__expected_version__}"
    body = context.page.text_content("body")
    assert body is not None
    assert expected in body


@then('I take a screenshot named "{name}"')
def step_take_screenshot(context, name):
    SCREENSHOTS_DIR.mkdir(exist_ok=True)
    context.page.screenshot(path=str(SCREENSHOTS_DIR / f"{name}.png"))
    context.page.close()
