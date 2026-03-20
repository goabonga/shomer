Feature: OIDC Discovery endpoint

  Scenario: Discovery endpoint returns 200 with issuer
    When I send a GET request to "/.well-known/openid-configuration"
    Then the response status code should be 200
    And the response body should contain "issuer"

  Scenario: Discovery returns authorization and token endpoints
    When I send a GET request to "/.well-known/openid-configuration"
    Then the response status code should be 200
    And the response should have JSON key "authorization_endpoint"
    And the response should have JSON key "token_endpoint"
    And the response should have JSON key "userinfo_endpoint"
    And the response should have JSON key "jwks_uri"

  Scenario: Discovery returns supported scopes and grants
    When I send a GET request to "/.well-known/openid-configuration"
    Then the response status code should be 200
    And the response body should contain "openid"
    And the response body should contain "authorization_code"
    And the response body should contain "S256"

  Scenario: Discovery includes Cache-Control header
    When I send a GET request to "/.well-known/openid-configuration"
    Then the response status code should be 200
    And the response should have header "Cache-Control" containing "max-age"

  Scenario: Discovery returns JSON content type
    When I send a GET request to "/.well-known/openid-configuration"
    Then the response status code should be 200
    And the response content type should be json
