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
    context.page.wait_for_load_state("domcontentloaded")
    body = context.page.text_content("body")
    assert body is not None, "Page body is None"
    assert text in body, f"'{text}' not found in page body"


@then("the page should contain the current version")
def step_check_page_version(context):
    expected = f"v{__expected_version__}"
    body = context.page.text_content("body")
    assert body is not None
    assert expected in body


@when('I fill "{selector}" with "{value}"')
def step_fill_input(context, selector, value):
    context.page.fill(selector, value)


@when('I click the "{text}" button')
def step_click_button(context, text):
    context.page.click(f"button:has-text('{text}')")
    context.page.wait_for_load_state("load", timeout=10000)
    context.page.wait_for_load_state("networkidle", timeout=10000)


@when('I click the "{text}" link')
def step_click_link(context, text):
    context.page.click(f"a:has-text('{text}')")
    context.page.wait_for_load_state("networkidle")


@then('the page URL should contain "{text}"')
def step_check_url(context, text):
    assert text in context.page.url, (
        f"URL '{context.page.url}' does not contain '{text}'"
    )


@then('I take a screenshot named "{name}"')
def step_take_screenshot(context, name):
    SCREENSHOTS_DIR.mkdir(exist_ok=True)
    context.page.screenshot(path=str(SCREENSHOTS_DIR / f"{name}.png"))
    context.page.close()
