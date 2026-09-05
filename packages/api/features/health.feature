# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

Feature: Liveness and discovery surface
  As an operator of shomer-api
  I want the deployed service to answer its liveness probe and publish a
  discovery document whose URLs resolve, so a load balancer can route to
  it and an OIDC client can find the endpoints without being told them.

  Background:
    Given shomer-api is reachable at SHOMER_API_URL

  Scenario: The liveness probe reports the running version
    When I GET "/healthz"
    Then the response status is 200
    And the JSON body has key "status" equal to "ok"
    And the JSON body has key "version" matching "^\d+\.\d+\.\d+$"

  Scenario: Discovery advertises the endpoints a client needs
    When I GET "/.well-known/openid-configuration"
    Then the response status is 200
    And the JSON body has key "issuer"
    And the JSON body has key "authorization_endpoint"
    And the JSON body has key "token_endpoint"
    And the JSON body has key "jwks_uri"
    And the JSON body has key "response_types_supported" containing "code"
    And the JSON body has key "grant_types_supported" containing "authorization_code"

  Scenario: Discovery requires PKCE
    # The platform serves public clients, which have nowhere to keep a
    # secret. Without PKCE such a client cannot prove the code it redeems
    # is the one it asked for, so advertising anything else here would be
    # telling clients they may skip the only proof they have.
    When I GET "/.well-known/openid-configuration"
    Then the JSON body has key "code_challenge_methods_supported" containing "S256"

  Scenario: Discovery URLs are absolute and share the issuer origin
    # A relative or differently-originned endpoint is the failure mode
    # this scenario exists for: it deploys cleanly, and every client that
    # compares `iss` byte-for-byte rejects the tokens.
    When I GET "/.well-known/openid-configuration"
    Then the discovery endpoints all start with the issuer
