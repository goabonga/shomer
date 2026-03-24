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
    context.page.wait_for_load_state("domcontentloaded", timeout=15000)
    body = context.page.text_content("body")
    assert body is not None, "Page body is None"
    assert text in body, f"'{text}' not found in page body"


@then("the page should contain the current version")
def step_check_page_version(context):
    expected = f"v{__expected_version__}"
    body = context.page.text_content("body")
    assert body is not None
    assert expected in body


@when('I navigate to "{path}"')
def step_navigate_to(context, path):
    """Navigate the current page to a new path (preserves cookies/session)."""
    context.page.goto(context.base_url + path)


@when('I fill "{selector}" with "{value}"')
def step_fill_input(context, selector, value):
    context.page.fill(selector, value)


@when('I attach file "{filename}" to "{selector}"')
def step_attach_file(context, filename, selector):
    """Attach a file to a file input element."""
    fixtures_dir = Path(__file__).parent.parent / "fixtures"
    file_path = fixtures_dir / filename
    context.page.set_input_files(selector, str(file_path))


@when('I select "{value}" from "{selector}"')
def step_select_option(context, value, selector):
    """Select an option from a dropdown by its visible label."""
    context.page.select_option(selector, label=value)


@when('I click the "{text}" button')
def step_click_button(context, text):
    context._last_navigation_url = ""
    _redirect_holder = []

    def _on_response(response):
        loc = response.headers.get("location", "")
        if response.status in (301, 302, 303) and loc:
            _redirect_holder.append(loc)

    context.page.on("response", _on_response)
    try:
        context.page.wait_for_selector(f"button:has-text('{text}')", timeout=5000)
        # Use expect_navigation to wait for any triggered navigation
        try:
            with context.page.expect_navigation(
                timeout=15000, wait_until="networkidle"
            ):
                context.page.click(f"button:has-text('{text}')")
        except Exception:
            # No navigation occurred (e.g. form validation error on same page)
            pass
        context.page.wait_for_load_state("domcontentloaded", timeout=15000)
    except Exception:
        pass

    if _redirect_holder:
        context._last_navigation_url = _redirect_holder[-1]

    try:
        context.page.remove_listener("response", _on_response)
    except Exception:
        pass


@when('I click the "{text}" link')
def step_click_link(context, text):
    context.page.click(f"a:has-text('{text}')")
    context.page.wait_for_load_state("load", timeout=10000)
    context.page.wait_for_load_state("networkidle", timeout=10000)


@then('the page URL should contain "{text}"')
def step_check_url(context, text):
    try:
        url = context.page.url
    except Exception:
        url = ""
    # Fallback to captured redirect URL (for external redirects like OAuth2 callback)
    nav_url = getattr(context, "_last_navigation_url", "")
    if text not in url and nav_url:
        url = nav_url
    assert text in url, f"URL '{url}' does not contain '{text}'"


@then('the page should have an element "{selector}"')
def step_check_element_exists(context, selector):
    """Check that a CSS selector matches at least one element on the page."""
    context.page.wait_for_load_state("domcontentloaded", timeout=15000)
    el = context.page.query_selector(selector)
    assert el is not None, f"No element found matching '{selector}'"


@then('I take a screenshot named "{name}"')
def step_take_screenshot(context, name):
    SCREENSHOTS_DIR.mkdir(exist_ok=True)
    try:
        context.page.screenshot(path=str(SCREENSHOTS_DIR / f"{name}.png"))
    except Exception:
        pass  # Page may be closed after external redirect
    try:
        context.page.close()
    except Exception:
        pass
