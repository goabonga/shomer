# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

Feature: The rendered frontend
  As a person signing in to Shomer
  I want the deployed frontend to render in a real browser and to carry
  the configuration the server resolved, so what I see is the deployment
  I am actually talking to.

  Background:
    Given shomer-ssr is reachable at SHOMER_SSR_URL

  Scenario: The shell renders through a browser
    # A TestClient proves the server returns HTML. It cannot prove the
    # bundle parses, mounts and paints — which is the half that breaks
    # when an asset ships stale or missing.
    When I open "/"
    Then the page heading is "Shomer"

  Scenario: A deep link renders the same shell
    # Every client route is served the same document; a 404 here would
    # mean a refresh on any inner page breaks.
    When I open "/somewhere/deep"
    Then the page heading is "Shomer"

  Scenario: The page carries the issuer the server resolved
    # Not a constant compiled into the bundle: the browser has to send
    # the user to the same origin the tokens will claim to come from.
    When I open "/"
    Then the runtime config key "issuer" is not empty
    And the runtime config key "version" matches "^\d+\.\d+\.\d+$"

  Scenario: The favicon is served as an image
    # Browsers request /favicon.ico unprompted. Falling through to the
    # catch-all answers 200 with an HTML document — a success that is not
    # an image, shows no icon, and leaves nothing to diagnose.
    When I request "/favicon.ico"
    Then the response content type is "image/x-icon"
